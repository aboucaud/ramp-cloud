# RAMP kits virtual image setup

This program aims deploying a RAMP pipeline with a given kit, on a virtual image.
Instances with that image can then be fired for each user submission to compute their predictions.

Currently only Amazon EC2 is supported. Microsoft Azure and Google Compute Engine will be next.

## Usage

1. install Packer (see [dedicated section](#Packer))

2. set up your cloud credentials (see [here](#Credentials))

3. select the `.json` config file corresponding to the backend provider (`aws | azure | gcloud`), as well as the hardware you need (`cpu | gpu`)

4. run Packer
   ```bash
   packer build -var ramp_kit_name=kit_name -var backend_data_dir=/path/to/data/ config.json
   ```
   Example command for creating the backend AWS AMI with pure CPU support for the `autism` starting kit; where the backend data files are stored in a local directory `./autism/testdata/`
   ```bash
   packer build -var ramp_kit_name=autism -var backend_data_dir=./autism/testdata/ aws_cpu_setup.json
   ```

## Packer

The kit environments on virtual machines (AWS, Azure, GCloud) are build using
[Packer](https://www.packer.io/). To create an image, the first step is to 
[install Packer](https://www.packer.io/intro/getting-started/install.html).

Packer uses a JSON configuration file called _template_ to specify the needs
for building an image. 

### Commands

-  check the configuration file
   ```bash
   packer validate config.json
   ```

-  create the image
   ```bash
   packer build config.json
   ```

### Template file

Configuration - _template_ - file example

```json
{
  "variables": {
    "aws_access_key": "",
    "aws_secret_key": ""
  },
  "builders": [
    {
      "type": "amazon-ebs",
      "access_key": "{{user `aws_access_key`}}",
      "secret_key": "{{user `aws_secret_key`}}",
      "region": "us-west-2",
      "source_ami": "ami-0bbe6b35405ecebdb",
      "instance_type": "t2.micro",
      "ssh_username": "ubuntu",
      "ami_name": "packer-hello-world"
    }
  ],
  "provisioners": [
    {
     "type": "shell",
     "inline": "echo \"Hello World!\"" 
    }  
  ]
}
```

The template files consist in three main sections,

- `variables`: which specifies the user variables and a default value. These 
   variables can be superseeded with environment variables (same name) 
   `MY_VAR=ramp` or directly in the build command line
   ```bash
   packer build -var my_var=ramp template.json
   ```

- `builders`: which is responsible for creating the machine and building the
   image. It has information on the platform, the base image, the image name,
   etc.

- `provisioners`: the list of actions to perform on the image before saving it.
   Among those, file upload/download, remote execution of shell commands and 
   shell scripts.


## Credentials

### Amazon EC2

In order for the Packer scheme to work seemlessly, one needs to set up 
local credentials in the form of a file `~/.aws/credentials` on Linux/macOS ; 
or `C:\Users\USERNAME\.aws\credentials` on Windows.

These credentials can be obtained in your Amazon account, see 
[this page][aws_setup] for help.

### Microsoft Azure 

[Azure setup][azure_setup]

### Google Cloud

[Google Compute Engine setup][gce_setup]



[aws_setup]: https://docs.aws.amazon.com/fr_fr/sdk-for-net/v2/developer-guide/net-dg-config-creds.html
[azure_setup]: https://www.packer.io/docs/builders/azure-setup.html
[gce_setup]: https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances
