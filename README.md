<p align="center">
  <img src="public/images/site-logo.png" width="400"/>
</p>

# Name of Article

TODO -> ADD SCREENSHOT OF A DOT DENSITY PLOT
TODO -> Describe Hack day, the Data Clinic's role, brief description of the articles purpose and the main hypotheses you explored (super brief)

### Getting started

This repository generates some of the statistics and visualizations included in this article TODO -> add link when it exists

#### Installations
Make sure you have Python 3.9 or above. You can check in the command line with python --version or python3 --version

To create a virtual environment within this head directory `cd EPA-HACK-DAY-ANALYSIS`, run `python3 -m venv venv`. The second "venv" can be any name of your virtual environment.

Run the following to activate virtual environment to use and disable to stop using:

bash (Mac OS, Linux): source venv/bin/activate
win (windows): venv\Scripts\activate.bat or venv\Scripts\activate.ps1 for powershell

`deactivate` will deactivate your virtual env

Once your environment is activated, run `python3 -m pip install -r requirements.txt`.

### Open Data Files

1.  First, visit the [Data Liberation Project EPA-RMP github page](https://github.com/data-liberation-project/epa-rmp-spreadsheets/tree/main/data/output) and download `submissions.csv`, `facilities.csv`, and `naics-codes.csv` and place them in `data/raw` in this project directory.
2.  Next, execute the pipeline by running `make all` in your terminal from the project directory.

### Processed Files
Running this pipeline will generate several data assets. 

-  `data/processed/facilities_geo` contains a cleaned and processed version of the RMP facilities dataset
- `data/processed/US_bg_census` contains block group level American Community Survey data for the entire US
-  `data/processed/urban_area_statistics.csv` contains the fenceline-to-city ratios for each city across our set of census metrics.
-  The folder `data/viz/` will contain sub-directories for each of the cities in our analysis. Inside these directories are the data files needed to produce the dot-density maps we include in the blog post.

### Directory Structure

TODO -> make something like you did for building emissions 

### Instructions for generating dot-density maps for any city

Once the pipeline has run and `data/viz/` has been populated, you can view dot density maps for any city by following these steps:

1.  Naviagate to `viz/dot_denisty.html` and replace the city defined in line 40 with the name of the `data/viz/` folder for the city you want to look at (e.g. `batonrouge` for Baton Rouge).
2.  Run `python -m http.server 8000` from the project home directory
3.  Open `http://localhost:8000/viz/dot_density.html` in your web browser.

You should see an interactive dot-density map marking the fenceline zone in your chosen city.

### Data Clinic
[Data Clinic](https://www.twosigma.com/data-clinic/) is the data and tech-for-good arm of [Two Sigma](https://twosigma.com), a financial sciences company headquartered in NYC. Since Data Clinic was founded in 2014, we have provided pro bono data science and engineering support to mission-driven organizations around the world via close partnerships that pair Two Sigma's talent and way of thinking with our partner's rich content-area expertise. To scale the solutions and insights Data Clinic has gathered over the years, and to contribute to the democratization of data, we also engage in the development of open source tooling and data products.