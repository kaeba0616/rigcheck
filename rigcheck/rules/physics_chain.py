"""물리 체인 검증: 입력→출력 순환(무한루프) 및 끊어진 체인 감지."""
from ..models import CheckResult, Finding, Severity
from ..parser import Live2DModel


def check_physics_chain(model: Live2DModel) -> CheckResult:
    """물리 설정의 입력→출력 체인이 순환하거나 끊어졌는지 검사한다."""
    result = CheckResult(rule_name="물리 체인 검증")

    if not model.physics_settings:
        result.findings.append(Finding(
            rule="physics_chain",
            severity=Severity.INFO,
            message="물리 설정 없음 — 체인 검사 불필요",
        ))
        return result

    # 물리 설정의 입력/출력 매핑 구축
    # setting_index -> (input_ids, output_ids)
    setting_io: list[tuple[set[str], set[str]]] = []

    for setting in model.physics_settings:
        input_ids = set()
        output_ids = set()

        for inp in setting.get("Input", []):
            src = inp.get("Source", {})
            if "Id" in src:
                input_ids.add(src["Id"])

        for out in setting.get("Output", []):
            dst = out.get("Destination", {})
            if "Id" in dst:
                output_ids.add(dst["Id"])

        setting_io.append((input_ids, output_ids))

    # 순환 감지: 어떤 설정의 출력이 다른 설정의 입력이 되고,
    # 그 설정의 출력이 다시 원래 설정의 입력이 되는 경우
    all_outputs = {}  # param_id -> setting_index
    for i, (_, outputs) in enumerate(setting_io):
        for out_id in outputs:
            all_outputs[out_id] = i

    # 그래프 기반 순환 탐지
    # 노드: 물리 설정 인덱스
    # 엣지: 설정 A의 출력이 설정 B의 입력에 포함되면 A -> B
    adjacency: dict[int, set[int]] = {i: set() for i in range(len(setting_io))}

    for i, (inputs, _) in enumerate(setting_io):
        for inp_id in inputs:
            if inp_id in all_outputs:
                src_setting = all_outputs[inp_id]
                if src_setting != i:
                    adjacency[src_setting].add(i)

    # DFS로 순환 탐지
    visited = set()
    in_stack = set()
    cycles = []

    def dfs(node, path):
        visited.add(node)
        in_stack.add(node)
        path.append(node)

        for neighbor in adjacency[node]:
            if neighbor in in_stack:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif neighbor not in visited:
                dfs(neighbor, path)

        path.pop()
        in_stack.remove(node)

    for node in range(len(setting_io)):
        if node not in visited:
            dfs(node, [])

    if cycles:
        for cycle in cycles:
            names = []
            for idx in cycle:
                setting = model.physics_settings[idx] if idx < len(model.physics_settings) else {}
                # 물리 사전에서 이름 찾기
                phys_dict = model.physics_meta.get("PhysicsDictionary", [])
                name = f"PhysicsSetting{idx+1}"
                if idx < len(phys_dict):
                    name = phys_dict[idx].get("Name", name)
                names.append(name)

            result.findings.append(Finding(
                rule="physics_chain",
                severity=Severity.WARNING,
                message=f"물리 체인 순환 감지: {' → '.join(names)}",
                details="물리 설정의 출력이 다시 입력으로 돌아가는 순환이 있습니다. "
                        "의도적인 피드백 루프가 아니라면 무한 진동을 유발할 수 있습니다.",
            ))

    # 고립된 물리 설정 감지 (입력도 출력도 다른 설정과 연결 안 됨)
    defined_params = {p["Id"] for p in model.parameters}
    for i, (inputs, outputs) in enumerate(setting_io):
        # 출력이 cdi3에 정의된 파라미터가 아닌 경우
        orphan_outputs = outputs - defined_params
        if orphan_outputs:
            phys_dict = model.physics_meta.get("PhysicsDictionary", [])
            name = f"PhysicsSetting{i+1}"
            if i < len(phys_dict):
                name = phys_dict[i].get("Name", name)

            result.findings.append(Finding(
                rule="physics_chain",
                severity=Severity.WARNING,
                message=f"물리 출력 참조 오류: {name}",
                details=f"출력 파라미터가 cdi3.json에 없음: {', '.join(orphan_outputs)}. "
                        f"물리 결과가 캐릭터에 반영되지 않습니다.",
            ))

    return result
