# OpenAlex

A collection of python tools to download, plot and export [OpenAlex][1] data in graph format.
[1]: https://openalex.org/

## Download

To download the data of articles published by an author,
you first need to know his OpenAlex ids.
If you only know his name,
you can use the following interactive command to save his ids,
one per row, in `authors.txt`.

```sh
$ ./download.py author "paul erdos" >> authors.txt
- page 1/1
Do you want to include Paul Erdős (Hungarian Academy of Sciences)? y/n y
Do you want to include Paul L. Erdos (unknown institution)? y/n n
Do you want to include PAUL ERDOS (unknown institution)? y/n n
Do you want to include Paul Erdös (unknown institution)? y/n n
```

To download the data of the works of the authors in `authors.txt`,
you can use:

```sh
./download.py works authors.txt > works.jsonl
```

To download the data of the articles cited by the works in `works.jsonl`,
you can use:

```sh
./download.py cited_by works.jsonl > cited_by.jsonl
```

To download the data of the articles that cite some work in `works.jsonl`,
you can use:

```sh
./download.py cites works.jsonl > cites.jsonl
```

All the works downloads can include duplicated items.
This can be due to, for example, a work being cited by two different works.
All the tools in this repository are implemented in such a way
that this fact does not alter the results
nor increase the number of queries required.
But if you want to use any external tool,
you may want to remove duplicated works:

```sh
sort works.jsonl | uniq > unique_works.jsonl
```

### Download options

All the previous commands accept the same options,
described in this section.

OpenAlex has a [polite pool][2] that is much faster
and gives more consistent response times.
To get into the polite tool,
you can set your email or api key with the `--email` or `--api-key` options.

When the result of a query is too big, OpenAlex paginates the response.
You can decide the number of results to include per page
with the `--per-page` option.
In principle, it can be up to 200.
But sometimes the server can not return so big results,
so it is recommended to use a smaller value.
The default is 50.

In case a query fails, you may want to retry it.
You can set the maximum number of retries with `--max-retries` (default: 0),
the factor to determine the delay between retries
with `--retry-backoff-factor` (default: 0.1),
and the HTTP error codes that trigger a retry
with `--retry-http-codes` (default: 429, 500 and 503).

Even with that, a query can fail.
To avoid having to restart the download from the beginning,
you can restart a query from the subquery and page were it stopped
with the options `-q` or `--start-query` (default: 1)
and `-p` or `--start-page` (default: 1).
As the result format is a jsonl where each line is an article,
you can just append the new results to the old ones:

```sh
./download.py cites works.jsonl -q 15 -p 4 >> cites.jsonl
```

In addition, every command in this repository has an option `-h` or `--help`
that shows a help message.

[2]: https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication#the-polite-pool

## Plot

You can plot an histogram of the number of citations in `cites.jsonl` per year
that cite the works in `works.jsonl` with the following command:

```sh
./plot.py works.jsonl cites.jsonl plot.pdf
```

By default, it plots the citations per year of publication of the cited work.
If you want to plot them per year of the publication of the work that cites,
you can add the option `-y` or `--per-year-of-citation`.

You can also color the citations by the cited work
with the options `-c works` or `--color works`,
and color them by the works that cites with `-c cites` or `--color cites`.
As too many colors can be needed,
you can limit the number of colors to be used
with the option `-n` or `--ncolors` (default: 10).
When this option is used,
less cited works or works that cite less are painted with the same color,
in order to only use the given number of colors.

## Export to graph

If you want to export the data of a works file to a graph,
you can use the `./graph.py` command.

You can use the option `-f` or `--format`
to choose between GML and GraphML as output format (default: GML).

You can produce the graph in two different ways:
the nodes can be the works or the authors.

### Works graph

This command will create a graph
where the nodes will be the works in `works.jsonl`,
and there will be an edge from a node A to a node B if A cites B.

```sh
./graph.py works works.jsonl graph_works.gml
```

For example, if you want to create a graph with
all the Erdős works, the works they cite, and the works that cite them,
you can use the following commands
with the files downloaded in the download section of this readme:

```sh
cat works.jsonl cites.jsonl cited_by.jsonl > all.jsonl
./graph.py works all.jsonl graph_works.gml
```

The edge metadata is just the date of publication of the work that cites.
The node metadata is, by default, the title, the publication date,
the authors, and the primary location.
You can change the node metadata with option `-m` or `--metadata`.
GraphML can store less metadata.

### Authors graph

A similar graph you can produce is the one where the nodes are the authors.

```sh
./graph.py authors all.jsonl graph_authors.gml
```

In this case, the weight of an edge from an author $a$ to an author $b$
is the probability (in percentage) that the author $a$ cites the author $b$:

```math
\frac{
  \sum_{i=2}^n \sum_{j=1}^{i-1} A_{i, a} \cdot A_{j, b} \cdot R_{i, j}
}{
  \sum_{i=2}^n \sum_{j=1}^{i-1} A_{i, a} \cdot A_{j, b}
} \cdot 100
```

where $n$ is the number of works,
$A_{i, a}$ is 1 if the $i$-th work (ordered by date of publication)
is authored by $a$ and 0 otherwise,
and $R_{i, j}$ is 1 if the $i$-th work references the $j$-th work.
