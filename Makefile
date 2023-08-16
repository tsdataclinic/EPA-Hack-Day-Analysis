.PHONY: all script1 script2 script3 script4 script5 script6 script7 script8 script9 script10

all: script10

preprocess_RMP:
	@echo "Running preprocess_RMP.py"
	python3 -m  src.data.preprocess_RMP

clean_RMP:
	@echo "Running clean_RMP.py"
	python3 -m  src.data.clean_RMP

download_census:
	@echo "Running download_census.py"
	python3 -m  src.data.download_census

interpolate_census:
	@echo "Running interpolate_census.py"
	python3 -m  src.analysis.interpolate_census

national_map:
	@echo "Running create_national_map_data.py"
	python3 -m  src.analysis.national_map

dot_plot_data:
	@echo "Running create_dot_plot_data.py"
	python3 -m  src.analysis.city_dot_density

all: preprocess_RMP clean_RMP download_census interpolate_census national_map dot_plot_data