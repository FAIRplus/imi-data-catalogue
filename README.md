# FAIRplus imi-data-catalogue

**Name:** FAIRplus catalogue for IMI projects and associated Datasets

**Goal:** Create a database of IMI funded **projects** and their associated **datasets**


**Current Seed:**
The existing [etriks - elixir IMI data catalogue](https://datacatalog.elixir-luxembourg.org)

**Known issues:**

  - [ ] Bias towards clinical trial data, not representative or suited for chemical structure description and the broad scope of IMI projects
    
  - [ ] The metadata model/structure is flat
   
  - [ ] Lack of data standards used for cataloguing (DCAT,...)
    
  - [ ] Lack of semantic markup (all free text) for key classifiers (identified by EFPIA partners) see issue #2


    * Scope clarity: 
      what is that we are cataloguing: Project AND Datasets
      * Project: should we index all known IMI projects listed from IMI site or only those FAIRplus (and eTRIKS) have engaged with?
      * Datasets: datasets are complex objects with many data modalities:
          * need to support versioning relevant for all prospective cases (i.e. new IMI2 engaging currently with FAIRplus) where       dataset releases (accrual datasets, longitudinal datasets ) are expected. 
      
            Note: for many finished projects, this is irrelevant (the retrospective use case

