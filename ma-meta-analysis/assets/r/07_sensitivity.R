library(meta)

if (exists("cont_model")) {
  cont_inf <- metainf(cont_model)
}

if (exists("bin_model")) {
  bin_inf <- metainf(bin_model)
}
