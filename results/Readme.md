##Results database for longish-running nnet training

This system, all in results.py, helps look after results from trainings of models.
I usually find that I present data to the model in blocks, which usually contain a few minibatches of training data and a small sample of test data.

#Using from training code
Two functions are provided which are called by the training routine:

#### `results.startRun`
This is called before any training, and stores information about the run for future reference. It also creates the database file (by default `results.sqlite`) if it doesn't exist.

`attribs` is a dictionary of properties to store for the run, `callerFilePath` is a list of filenames whose contents we store - e.g. the code. `continuation` is a string - I use the nonemptiness of `continuation` to indicate that the model was not trained from scratch, but from the saved weights of the previous run. `architecture` and `solver` are basically assumed in diffRuns and describeRun to be long JSON strings. You can change any of this.

#### `results.step`
This stores the reported training and test objective and accuracy from each step of training.
These are stored in the STEPS table.
The time for the first 10 steps (excluding the first) is remembered in the steps table.

Similar functions are also available in lua after something like this.
```
results = require 'results'
```

##warning
Only one process should modify the database at any one time; you cannot train two models to the same database. But you can have as many processes as you like connected to the database and using the query functions, even during training.

#Using the results
I usually have an alias like `ipython -i -c "import numpy as np; import results as r"`.
The following functions are easy to use analysis functions.
* `r.runList()` and `r.runList2()` provide summaries of all the runs.
* `r.plotRun(x)` draws a graph of the training of the xth run
* `r.plotRuns(x,y)` draws a graph comparing the training of two runs
* `r.rrs(x,y)` is a text mode comparison of how two runs' training compare.
* `r.describeRun(x)` prints the information which `startRun` supplied
* `r.diffRuns(x,y)` makes a comparison of the startRun info of two runs
* `r.steps(x)` prints a table of all the steps
* `r.lastSteps()` prints a table of all the steps of the latest (e.g. current) run
* `r.l()` is a very small summary of whether the latest (e.g. current) run is making progress.

It can be desirable to take moving averages of the accuracy and error. Only `runList2` does this by default.

At the moment whether to draw graphs on screen or to file is determined by the `oncampus` module in this repo. This will want modifying for other users, as well as the file location used (in `pushplot`).