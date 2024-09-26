import json
import os
import tempfile
from unittest import mock

import pytest

from taca.element import Element_Runs as to_test

CONFIG = {
    "element_analysis": {
        "Element": {
            "GenericElement": {
                "demux_dir": "mock_demux_dir_path",
                "transfer_log": "mock_transfer_log_file.log",
            },
        },
    },
}


def create_element_run_dir(
    tmp: tempfile.TemporaryDirectory,
    run_name: str = "20240716_AV242106_testrun",
    nosync: bool = False,
    run_finished: bool = True,
    sync_finished: bool = True,
    demux_dir: bool = True,
    n_demux_subdirs: int = 1,
    demux_done: bool = True,
    outcome_completed: bool = True,
) -> str:
    """
    Conditionally build a file tree for an Element run.

        .
        ├── RunManifest.csv
        ├── RunManifest.json
        ├── RunParameters.json
        ├── RunUploaded.json
        ├── .sync_finished
        ├── Demultiplexing
            ├── Demultiplexing_0
            |   └── RunStats.json
            ├── Demultiplexing_1
            |   └── RunStats.json
            └── ...

    """

    # Create run dir
    if nosync:
        run_path = f"{tmp.name}/ngi_data/sequencing/AV242106/nosync/{run_name}"
    else:
        run_path = f"{tmp.name}/ngi_data/sequencing/AV242106/{run_name}"
    os.mkdir(run_path)

    # Populate run dir with files and folders
    if run_finished:
        open(f"{run_path}/RunManifest.csv", "w").close()
        open(f"{run_path}/RunManifest.json", "w").close()
        open(f"{run_path}/RunParameters.json", "w").close()
        with open(f"{run_path}/RunUploaded.json", "w") as f:
            outcome = "OutcomeCompleted" if outcome_completed else "OutcomeFailed"
            f.write(json.dumps({"outcome": outcome}))

    if sync_finished:
        open(f"{run_path}/.sync_finished", "w").close()

    if demux_dir:
        os.mkdir(os.path.join(run_path, "Demultiplexing"))
        for i in range(n_demux_subdirs):
            os.mkdir(os.path.join(run_path, "Demultiplexing", f"Demultiplexing_{i}"))
            if demux_done:
                open(
                    os.path.join(
                        run_path,
                        "Demultiplexing",
                        f"Demultiplexing_{i}",
                        "RunStats.json",
                    ),
                    "w",
                ).close()

    return run_path


@mock.patch("taca.element.Element_Runs.ElementRunsConnection")
class TestRun:
    def test_init(self, mock_db: mock.Mock, create_dirs: pytest.fixture):
        tmp: tempfile.TemporaryDirectory = create_dirs
        run_dir = create_element_run_dir(tmp)

        run = to_test.Run(run_dir, CONFIG)
        assert run.run_dir == run_dir

    @pytest.mark.parametrize(
        "p",
        [
            {"run_finished": True, "outcome_completed": True, "expected": True},
            {"run_finished": True, "outcome_completed": False, "expected": False},
            {"run_finished": False, "outcome_completed": False, "expected": False},
        ],
        ids=["success", "failure", "ongoing"],
    )
    def test_check_sequencing_status(
        self,
        mock_db: mock.Mock,
        p: pytest.fixture,
        create_dirs: pytest.fixture,
    ):
        tmp: tempfile.TemporaryDirectory = create_dirs

        run = to_test.Run(
            create_element_run_dir(
                tmp,
                run_finished=p["run_finished"],
                outcome_completed=p["outcome_completed"],
            ),
            CONFIG,
        )
        assert run.check_sequencing_status() is p["expected"]

    @pytest.mark.parametrize(
        "p",
        [
            {"demux_dir": False, "demux_done": False, "expected": "not started"},
            {"demux_dir": True, "demux_done": False, "expected": "ongoing"},
            {"demux_dir": True, "demux_done": True, "expected": "finished"},
        ],
        ids=["not started", "ongoing", "finished"],
    )
    def test_get_demultiplexing_status(
        self, mock_db: mock.Mock, p: pytest.fixture, create_dirs: pytest.fixture
    ):
        tmp: tempfile.TemporaryDirectory = create_dirs

        run = to_test.Run(
            create_element_run_dir(
                tmp,
                demux_dir=p["demux_dir"],
                demux_done=p["demux_done"],
            ),
            CONFIG,
        )
        assert run.get_demultiplexing_status() == p["expected"]

    @pytest.mark.parametrize(
        "p",
        [
            {"run_finished": True, "expected": True},
            {"run_finished": False, "expected": False},
        ],
        ids=["exists", "does not exist"],
    )
    def test_manifest_exists(
        self, mock_db: mock.Mock, create_dirs: pytest.fixture, p: pytest.fixture
    ):
        tmp: tempfile.TemporaryDirectory = create_dirs

        run = to_test.Run(
            create_element_run_dir(
                tmp,
                run_finished=p["run_finished"],
            ),
            CONFIG,
        )
        assert run.manifest_exists() == p["expected"]

    @pytest.mark.skip(reason="Not implemented yet")
    def test_generate_demux_command(self, mock_db):
        pass

    def test_start_demux(self, mock_db, create_dirs):
        with mock.patch(
            "taca.utils.misc.call_external_command_detached"
        ) as mock_call, mock.patch(
            "taca.element.Element_Runs.Run.generate_demux_command"
        ) as mock_command:
            mock_command.return_value = "test command"
            run = to_test.Run(create_element_run_dir(create_dirs), CONFIG)
            run.start_demux()
            mock_command.assert_called_once()
            mock_call.assert_called_once_with(
                "test command", with_log_files=True, prefix="demux_"
            )

    @pytest.mark.skip(reason="Not implemented yet")
    def test_is_transferred(self, mock_db, create_dirs):
        pass

    @pytest.mark.skip(reason="Not implemented yet")
    def test_parse_rundir(self, mock_db, create_dirs):
        pass
