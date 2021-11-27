- we restrict our file selection to .go files
- we only consider files that were present at the start and end commit (note: we lose some files due to file structure 
    changes)

- currently our timeframe is arbitrarily chosen (2019 - now). we need to find and motivate a meaningful timeframe 
    (maybe since last release?)

- taking delta_nloc as complexity measure for task 1 might not be ideal. what about the scenario of a file that gets 
    modified a lot (sometimes code gets added, sometimes deleted) and in the end the delta of nloc is the same.
    maybe its better to take just the end amount of nloc as a complexity measure of the file.