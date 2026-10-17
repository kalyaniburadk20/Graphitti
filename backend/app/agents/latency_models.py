from dataclasses import dataclass, field


@dataclass
class StageTiming:
    stage: str
    duration_ms: float


@dataclass
class RunMetrics:

    total_ms: float = 0.0

    stages: list[StageTiming] = field(
        default_factory=list
    )

    def add_stage(
        self,
        stage: str,
        duration_ms: float,
    ):
        self.stages.append(
            StageTiming(
                stage=stage,
                duration_ms=round(
                    duration_ms,
                    2,
                ),
            )
        )

    def get_stage_time(
        self,
        stage: str,
    ) -> float:

        for item in self.stages:

            if item.stage == stage:
                return item.duration_ms

        return 0.0