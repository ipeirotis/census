# Address Intelligence Microservice using Census Data


The [ACS5 census data set](https://www.census.gov/programs-surveys/acs/guidance/subjects.html) provides a significant amount of information about the households and the population that lives in a particular location. Specifically, the ACS5 dataset provides details at the _census tract_ level, and gives information about age, race, income, marital status, fertility,  house ownership, mobility, house value, rent value, education,  and other useful information. [See an example using the Census Reporter website (by Knight Foundation)](https://censusreporter.org/profiles/14000US36061003300-census-tract-33-new-york-ny/)

This microservice provides a curated access to the underlying census information, focusing on variables of interest. 

## Technical Details

* The service runs on Google Cloud, under Panos's account. Project ID: `rock-idiom-260222`.

* The service runs at `census.ipeirotis.com` port 5000.

* Encryped the client-secrets file by logging to travis using the command:
    * `travis login --org --github-token [GITHUB TOKEN FOR LOGIN]"
    * `travis encrypt-file google-cloud-credentials.json --add --pro` 