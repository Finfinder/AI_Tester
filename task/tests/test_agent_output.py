from task import agent_output


def test_sum_list():
    assert agent_output.sum_list([1,2,3]) == 6


def test_sum_list_empty():
    assert agent_output.sum_list([]) == 0
