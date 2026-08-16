from pathlib import Path

from helios.checks.ferrum_wes_outputs import FerrumWesDrsOutputCheck
from helios.core.run_context import RunContext


def _ctx(**kwargs: object) -> RunContext:
    return RunContext(
        pipeline_name="demo",
        executor="nextflow",
        work_dir=Path("."),
        output_dir=Path("."),
        **kwargs,
    )


def test_pass_when_drs_uris_present() -> None:
    result = FerrumWesDrsOutputCheck().run(
        _ctx(metadata={"ferrum_wes_outputs": "drs://ferrum.example/obj-9"})
    )
    assert result.status == "pass"
    assert "obj-9" in result.evidence["drs_refs"][0]


def test_fail_when_wes_claimed_without_drs() -> None:
    result = FerrumWesDrsOutputCheck().run(_ctx(metadata={"wes_run_id": "run-1"}))
    assert result.status == "fail"


def test_skip_without_wes_context() -> None:
    result = FerrumWesDrsOutputCheck().run(_ctx())
    assert result.status == "skip"
