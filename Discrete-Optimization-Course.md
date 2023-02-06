<!-- ---
title: "Boxes with pandoc-latex-environment and tcolorbox"
author: [Author]
date: "2020-01-01"
subject: "Markdown"
keywords: [Markdown, Example]
lang: "en"
colorlinks: true
header-includes:
- |
  ```{=latex}
  \usepackage{tcolorbox}

  \newtcolorbox{info-box}{colback=cyan!5!white,arc=0pt,outer arc=0pt,colframe=cyan!60!black}
  \newtcolorbox{warning-box}{colback=orange!5!white,arc=0pt,outer arc=0pt,colframe=orange!80!black}
  \newtcolorbox{error-box}{colback=red!5!white,arc=0pt,outer arc=0pt,colframe=red!75!black}
  ```
pandoc-latex-environment:
  tcolorbox: [box]
  info-box: [info]
  warning-box: [warning]
  error-box: [error]
fontfamily: lato
fontfamilyoptions:
  - default
  - defaultsans
--- -->
---
title: Cool report title
author: John Doe
date: January 1970
toc: false
numbersections: true
geometry: margin=2.5cm
urlcolor: blue
header-includes: |
    \usepackage{fancyhdr}
    \usepackage{tcolorbox}
    \pagestyle{fancy}
    \lfoot{Draft Prepared: 1 January 1970}
include-before:
- '`\newpage{}`{=latex}'
---

\pagebreak
\tableofcontents
\pagebreak

# Discrete Optimization

## Knapsack

### Greedy algorithms

Many possible implementations to solve the same problem. For knapsack in
particular we could come up with: more valuable is better, more items is better, more value per kg is
better.

Zero guarantees that the problem is optimally solved. The problem needs to be
easy. We can use a quick and dirty greedy algorithm to get started with a
problem.

### Modelling

How to model, in general:

1. Select some **decision variables**, which encode the result we are interested
   in.
2. Express the **constraints** in terms of the decision variables.
3. Declare an **objective function**, which specifies the quality of each solution.

As a result, the optimization model we get is declarative (_what_, not _how_),
therefore there may be multiple ways to solve it.

Applying this to the knapsack problem:

1. Decision variables:
    - $x_i$ denotes whether item $i$ is selected from a set of items $S$.
        - $x_i=1$ means its selected.
        - $x_i=0$ means its not selected.
2. Constraints:
    - Selected items cannot exceed the capacity:

    $$
    \sum_{i \in S}w_i x_i \leq K
    $$

3. Objective function: total value of the selected items.

    $$
    \begin{aligned}
    \sum_{i \in S}v_i x_i
    \end{aligned}
    $$

This leaves us with the following model: maximize $\displaystyle\sum_{i \in
S}v_i x_i$ subject to



$$
  \sum_{i \in S}w_i x_i \leq K
$$
$$
  x_i \in \{0,1\} \space (i \in S)
$$

### Dynamic programming

Can be applied to problems that have a _optimal substructure_ and _overlapping subproblems_ (an optimal
solution can be constructed from optimal solutions of its subproblems).
For instance, given an optimal path $A \rightarrow C$, its subset $A \rightarrow
B$ must be the optimal path since there is a recurrent relationship.

Dynamic programming can be implemented either top-down or bottom-up. Storing
subproblem solutions is called memoization, which is obviously desirable.

For the knapsack problem, complexity is exponential $O(2^n)$, but the problem
definition lends itself to use dynamic programming. Considering a previous
knapsack problem solution with $n$ items, the solution to a new problem with
$n+1$ items, where this new item has weight $w_{n+1}$ and our capacity $K$ remains
the same, will be the one
that maximizes the objective function (as per our previous model) while satisfying
the constraints.

### Branch and bound

This method guarantees that an optimal solution is found without having to
evaluate all possible solutions. One of many possible search strategies are
_depth-first_, _best-first_ and _least-discrepancy_.

A **relaxation** is an approximation of a difficult problem by a nearby problem
that is easier to solve. This estimate will be the basis for more sophisticated
algorithms like branch and bound.

For the knapsack, this may be relaxing a constraint
such as the capacity $K$, which translates to "select all items". This one is
not very effective since not many of the tree branches are pruned.
We could also apply **linear relaxation**, which relaxes the integrality
requirement, i.e. we could take a fraction of any item, leaving us with the  $0 \leq x_i \leq 1
\space (i \in I)$ constraint instead of $x_i \in \{0,1\} \space (i \in S)$.

#### Depth-first

This strategy prunes when a node estimation is worse than the best found
solution so far.
It is memory efficient since we only handle a branch at any particular time.
Maximizing with the linear relaxation constraint leads us to a more accurate estimate, which in
turn will allow us to reduce the overall search space by stopping early at
unfeasible branches. With a naive relaxation like unlimited capacity, the
estimate would be higher and therefore prevent us from early pruning.

#### Best-first

A greedy strategy that selects the best node based on an estimate. Works best when the relaxation is
accurate and we can stop expanding nodes early, else it is very inefficient
memory-wise since for the worst case we have to visit all nodes. Time complexity
is of $O(b^m)$, given by a branching factor and maximum node depth $m$.

#### Limited discrepancy

This strategy assumes the heuristic is correct at all times. Let's say our heuristic is that
the left node is the correct one in every branch. Nodes are still pruned based on the estimate, as usual. The first search wave will
traverse the tree top-down picking the left-most node (0 mistakes). The second
wave must have 1 mistake, meaning the heuristic is followed but purposefully
ignored at one node.

Based on the implementation, we can have a memory efficient search but by doing
redundant computations or vice versa.

### Constraint programming

It is a complete method, not heuristic:
  - With enough time, it will find a feasible solution (one).
  - With enough time, it will find an optimal solution (all).

