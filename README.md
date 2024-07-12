# flood-impact-inputs
This model takes all of the parameter/ input data from the user specifically for the urban flooding workflow. 
This data is then propogated through the model, reducing user input. 

## Description
All data/ choices made by the user are inputted at this stage of the model to reduce user error. 
This process simplifies the user input methods.

## Input Parameters
*Location
  * Description: 


## Input Files (data slots)
* Boundary
  * Description: A .gpkg of the geographical area of interest. 
  * Location: /data/boundary
* SSP Datasets
  * Description: zipped outputs for all of the SSP scenario UDM outputs.
  * Location: /data/ssps

## Outputs
The model should output a csv containing a list of all parameters and user responses.
The boundary file, renamed after the chosen location.
