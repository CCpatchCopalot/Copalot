import json
import re
import subprocess
import sys
import tempfile
from enum import Enum
from tqdm import tqdm

sys.path.append('../..')


class FaultType(Enum):
    SUCCESS = "SUCCESS"
    NO_FIX = "NO_FIX"
    PLACEHOLDER = "PLACEHOLDER"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    AST_ERROR = "AST_ERROR"
    SAME_TO_DIFF = "SAME_TO_DIFF"
    SIM_DIFF = "SIM_DIFF"


class Fault:
    def __init__(self, type: FaultType, description: str | None = None, key: str | None = None):
        self.key = key
        self.type = type
        self.description = description


def clang_tidy_report(code: str) -> list[str]:
    code_file = tempfile.NamedTemporaryFile(mode='w', suffix=".c")
    report_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml")
    code_file.write(code)
    code_file.flush()
    result = subprocess.run(
        ["clang-tidy", code_file.name, f"--export-fixes={report_file.name}", "--extra-arg=-ferror-limit=0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(report_file.name) as f:
        report = yaml.safe_load(f)
    error_messages = []
    if report is None:
        return error_messages
    for diag in report["Diagnostics"]:
        error_level = diag["Level"]
        if error_level != "Error":
            continue
        diag_message = diag["DiagnosticMessage"]["Message"]
        error_messages.append(diag_message)
    return error_messages

def clang_tidy_check(code: str, ignore_error_message: list[str] = []) -> Fault:
    code_file = tempfile.NamedTemporaryFile(mode='w', suffix=".c")
    report_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml")
    code_file.write(code)
    code_file.flush()
    result = subprocess.run(
        ["clang-tidy", code_file.name, f"--export-fixes={report_file.name}", "--extra-arg=-ferror-limit=0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(report_file.name) as f:
        report = yaml.safe_load(f)
    if report is None:
        return Fault(FaultType.SUCCESS)
    for diag in report["Diagnostics"]:
        error_level = diag["Level"]
        if error_level != "Error":
            continue
        diag_message = diag["DiagnosticMessage"]["Message"]
        if diag_message in ignore_error_message:
            continue
        if diag_message.startswith("use of undeclared identifier"):
            # check identifier is constant
            matches = re.findall(r"'(.*?)'", diag_message)
            if len(matches) != 0:
                identifier = matches[0]
                if identifier.isupper():
                    continue
        elif "too many errors emitted" in diag_message:
            continue
        diag_name = diag["DiagnosticName"]
        offset = diag["DiagnosticMessage"]["FileOffset"]
        line = code[:offset].count("\n") + 1
        desp = f"There is a syntax error in line {line}: {diag_message}"
        return Fault(FaultType.SYNTAX_ERROR, desp)
    return Fault(FaultType.SUCCESS)


def checking(pa: str, pb: str, pc:list[str], pC: list[int] | None = None) -> Fault:
    ignore_error_message = clang_tidy_report(pa)
    fault = clang_tidy_check(pb, ignore_error_message)
    if fault.type != FaultType.SUCCESS:
        if not pC:
            return fault  # No changes to attempt recovery
        Pool = pC.copy()  # Pending recovery statements pool
        max_iterations = 100
        stagnant_iterations = 0
        prev_fault_count = 1  # Since fault.type is not SUCCESS, there is at least 1 fault
        recovered_pb = pb
        applied_pieces = []
        for iteration in range(max_iterations):
            if not Pool:
                break
            statement = Pool.pop(0)
            applied_pieces.append(pc[statement-1])
            recovered_pb = pb + "\n" + "\n".join(applied_pieces)
            current_fault = clang_tidy_check(recovered_pb, ignore_error_message)
            if current_fault.type == FaultType.SUCCESS:
                print(f"Recovered after {iteration + 1} iterations.")
                return recovered_pb
            if current_fault.type == fault.type:
                stagnant_iterations += 1
                if stagnant_iterations >= 5:
                    print("No improvement after 5 iterations, stopping recovery.")
                    break
            else:
                stagnant_iterations = 0
                fault = current_fault  # Update to the new reduced fault
        print("Recovery stopped due to limits or no progress.")
    return pb