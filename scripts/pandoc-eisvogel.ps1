if ($null -eq $args[0]) {
  Write-Output "no input doc defined"
  exit 1
}

pandoc $args[0] -o "eisvogel-document.pdf" --from markdown --template "pandoc-templates/eisvogel.tex" --filter pandoc-latex-environment --listings


# SEE https://github.com/Wandmalfarbe/pandoc-latex-template
# https://github.com/Wandmalfarbe/pandoc-latex-template/tree/master/examples/boxes-with-pandoc-latex-environment-and-tcolorbox
# pip install pandoc-latex-environment globally
