if ($null -eq $args[0]) {
  Write-Output "no input doc defined"
  exit 1
}

pandoc $args[0] --mathjax --toc --wrap=preserve -o out.pdf


