# Sample benchmark for AI_Tester
# Defines `cases` list consumed by evals_integration.local_run

cases = [
    {'input': [1,2,3], 'expected': 6},
    {'input': [], 'expected': 0},
]

meta = {
    'name': 'sum_list_simple',
    'description': 'Verify sum_list sums numbers in a list',
}

# The local runner expects `cases` and optional `meta` variables.
