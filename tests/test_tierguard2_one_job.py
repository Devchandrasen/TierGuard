import pytest

from scripts.submit_tierguard2_one_job import selected_job_ids, check_no_prior_attempt


def test_one_job_guard_accounts_for_every_selected_live_job():
    assert selected_job_ids("39247.mgmt01\n39248.mgmt01\n") == [
        "39247.mgmt01", "39248.mgmt01",
    ]


def test_one_job_guard_accepts_empty_queue_but_rejects_unknown_response():
    assert selected_job_ids("\n") == []
    with pytest.raises(ValueError, match="Unrecognized"):
        selected_job_ids("server unavailable")
    with pytest.raises(ValueError, match="Unrecognized"):
        selected_job_ids("39247[].mgmt01")


def test_one_job_guard_refuses_incomplete_previous_attempt(tmp_path):
    cell = tmp_path / "distributed_backdoor/alpha_0.3/mal_0.2/seed_2001/attempt"
    cell.mkdir(parents=True)
    with pytest.raises(ValueError, match="Prior attempt"):
        check_no_prior_attempt(tmp_path, "distributed_backdoor", 2001)
