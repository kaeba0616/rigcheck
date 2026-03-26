"""RigCheck 검사 엔진."""
from .models import Report
from .parser import Live2DModel, parse_model
from .rules import ALL_RULES


def run_check(runtime_dir: str) -> Report:
    """runtime 디렉토리를 검사하고 리포트를 생성한다."""
    model = parse_model(runtime_dir)
    report = Report(model_name=model.name)

    for rule_fn in ALL_RULES:
        result = rule_fn(model)
        report.results.append(result)

    return report
