### Getting started

This repository underlies the analysis posted at [enter link when it exists]. To reproduce our analysis, set up your and envirorment using `requirements.txt` and follow these two steps:

1.  First, visit the [Data Liberation Project EPA-RMP github page](https://github.com/data-liberation-project/epa-rmp-spreadsheets/tree/main/data/output) and download `submissions.csv`, `facilities.csv`, and `naics-codes.csv` and place them in `data/raw` within the project directory.
2.  Next, execute the pipeline by running `make all` from the project directory. 

Running this pipeline will generate several data assets. 

-  `data/processed/facilities_geo` contains a cleaned and processed version of the RMP facilities dataset
- `data/processed/US_bg_census` contains block group level American Community Survey data for the entire US
-  `data/processed/urban_area_statistics.csv` contains the fenceline-to-city ratios for each city across our set of census metrics.
-  The folder `data/viz/` will contain sub-directories for each of the cities in our analysis. Inside these directories are the data files needed to produce the dot-density maps we include in the blog post.

### Instructions for dot-density maps

Once the pipeline has run and `data/viz/` has been populated, you can view dot density maps for any city by following these steps:

1.  Naviagate to `viz/dot_denisty.html` and replace the city defined in line 40 with the name of the `data/viz/` folder for the city you want to look at (e.g. `batonrouge` for Baton Rouge).
2.  Run `python -m http.server 8000` from the project home directory
3.  Open `http://localhost:8000/viz/dot_density.html` in your web browser.

You should see an interactive dot-density map marking the fenceline zone in your chosen city.

