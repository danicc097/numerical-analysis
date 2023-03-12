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

# Convex Optimization I

## Notation

1. ${A|B}$, sometimes written ${A:B}$ means "the set of all A
  such that B."
  The logical disjunction is often just written as "or", although ∨
  is also common in more formal settings.



## Introduction

### Least squares

How do we know a problem is least squares? Are we asked to minimize the two norm
squares of an affine function of $x$, i.e. $f(x) = ax+b$? Then yes, else no...

### Convex optimization

$$
\begin{gathered}
\text{minimize} \space f_0(x)
\\[1em]
\text{subject to} \space f_i(x) \le b_i, i = 1,...,m
\end{gathered}
$$

and all these functions and its constraints have to be convex, i.e.

$$
\begin{gathered}
f_i(\alpha x+\beta y) \le \alpha f_i(x) + \beta f_i(y)
\\[1em]
\text{if } \space \alpha + \beta = 1, \space \alpha \ge 0 , \space \beta \ge 0
\end{gathered}
$$

![](images/2023-03-12-11-56-58.png)

the case of linear programming can be seen as an extreme case of convex
optimization where

$$
f_i(\alpha x+\beta y) = \alpha f_i(x) + \beta f_i(y)
$$

since any affine function is just at the limit of being either convex or concave.


# Affine set

An **affine set** contains a line through
any two distinct points in the set.

Given the example line $x=\theta x_1+(1-\theta)x_2$ verify that the solution set of a set of linear equations $\{x |
Ax+b=0\}$ is an affine set.

$$
Ax_1=b \\
Ax_2=b \\[1em]
\begin{aligned}
Ax&=A(\theta x_1 + (1-\theta)x_2) \\
&= \theta b + (1-\theta)b \\
&= b
\end{aligned}
$$
