"""
-=# Amazon EC2 command-line helper #=-

Currently supported actions:

- list the EC2 instances by state (default is 'running')

    $ python aws.py instance list [--state <state>]

- create an EC2 instance with a specific AMI

    $ python aws.py instance create <ami-id>

- list the registered AMIs

    $ python aws.py ami list

- given an AMI ID, print the corresponding name

    $ python aws.py ami name <ami-id>

- deregister a given AMI from EC2

    $ python aws.py ami delete <ami-id> [--dry-run]

"""
import sys

import click
import boto3
from botocore.exceptions import ClientError

INSTANCE_STATES = ['running', 'stopped', 'pending',
                   'shutting-down', 'terminated', 'stopping']


def get_amis():
    ec2 = boto3.resource('ec2')
    return ec2.images.filter(Owners=["self"])


def get_instance(id):
    ec2 = boto3.resource('ec2')
    return ec2.Instance(id=id)


def get_instances(state='running'):
    ec2 = boto3.resource('ec2')
    return ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': [state]}])


def create_instance(ami_id, key, itype='t2.micro'):
    ec2 = boto3.resource('ec2')
    instance_list = ec2.create_instances(
        ImageId=ami_id,
        InstanceType=itype,
        KeyName=key,
        MinCount=1,
        MaxCount=1
        )

    return instance_list[0]


def delete_ami(ami_id: str, dry_run: bool):
    ec2 = boto3.client('ec2')
    was_successful = False
    try:
        ec2.deregister_image(ImageId=ami_id, DryRun=dry_run)
        if not dry_run:
            was_successful = True
    except ClientError as e:
        if dry_run and e.response['Error'].get('Code') == 'DryRunOperation':
            was_successful = True
        else:
            print(e)

    return was_successful


@click.group(context_settings={'help_option_names': ['-h', '--help']},
             help=__doc__)
def cli():
    pass


@cli.group()
def ami():
    "Manages AWS AMI"


@ami.command('create')
@click.option('-n', '--kit-name', type=str, required=True,
              help=("RAMP kit name. Must be available as a repository on "
                    "https://github.com/ramp_kits"))
@click.option('-d', '--data-dir', type=click.Path(exists=True), required=True,
              help="Directory containing the training|testing data")
@click.option('-b', '--backend', type=click.Choice(['aws']),
              default='aws', show_default=True,
              help="Choice of backend")
@click.option('-c', '--compute-type', type=click.Choice(['cpu', 'gpu']),
              default='cpu', show_default=True,
              help="Choice of computing type")
@click.option('-s', '--suffix', type=str,
              default='backend', show_default=True,
              help="Suffix of the AMI name")
def ami_create(kit_name: str, data_dir: str, backend: str,
               compute_type: str, suffix: str):
    "Create an AMI for a RAMP kit"
    # Make sure to only rsync the files and not the directory
    if not data_dir.endswith('/'):
        data_dir += '/'

    options = " ".join([
        f"-var ramp_kit_name={kit_name}",
        f"-var backend_data_dir={data_dir}",
        f"-var ami_suffix_name={suffix}"
    ])
    config = f"{backend}_{compute_type}_setup.json"

    cmd = f"packer build {options} {config}"

    click.echo("Run the following command:")
    click.echo(cmd)


@ami.command('list')
def ami_list():
    "List the registered AMIs"
    out_template = "{id:<24} | {name}"
    click.echo(out_template.format(name="AMI Name", id="AMI ID"))
    click.echo('-' * 54)
    for ami in get_amis():
        click.echo(out_template.format(name=ami.name, id=ami.id))


@ami.command('name')
@click.argument('ami_id', type=click.STRING)
def ami_name(ami_id):
    "Print the name of a registered AMI"
    ami_found = False
    for ami in get_amis():
        if ami.id == ami_id:
            ami_found = True
            click.echo(ami.name)

    if not ami_found:
        click.echo("No registered AMI found with this ID")


@ami.command('delete')
@click.argument('ami_id', type=click.STRING)
@click.option('--dry-run', is_flag=True,
              help='Practice run to check whether this action '
                   'can be performed')
def ami_delete(ami_id: str, dry_run: bool):
    "Delete a registered AMI"
    current_ami_ids = [ami.id for ami in get_amis()]
    if ami_id not in current_ami_ids:
        msg = ("Provided AMI id invalid. Use the ami-list command to check "
               "for AMIs belonging to you.")
        sys.exit(click.echo(msg))

    success = delete_ami(ami_id, dry_run)
    if success:
        if dry_run:
            msg = "{} would have been successfuly deleted.".format(ami_id)
            click.echo(msg)
        else:
            click.echo("{} successfuly deleted.".format(ami_id))
    else:
        click.echo("{} could not be deleted.".format(ami_id))


@cli.group()
def instance():
    "Manages AWS instances"


@instance.command('list')
@click.option('--state', default='running',
              type=click.Choice(INSTANCE_STATES))
def instance_list(state: str):
    "List the current instances on AWS"
    out_template = "{id:<20} | {ami:<24} | {type:<15} | {key:<15} | {dns}"
    click.echo(out_template.format(
        id="Instance ID",
        ami="AMI ID",
        type="Instance type",
        key="SSH Key",
        dns="Public DNS name"))
    click.echo('-' * 130)

    for instance in get_instances(state):
        click.echo(out_template.format(
            id=instance.id,
            ami=instance.image_id,
            type=instance.instance_type,
            key=instance.key_name,
            dns=instance.public_dns_name))


@instance.command('create')
@click.argument('ami_id', type=click.STRING)
@click.option('-k', '--key', type=click.STRING, default='alexandre',
              help="Name of the secret key pair")
@click.option('-t', '--type', type=click.STRING, default='t2.micro',
              help="EC2 instance type")
def launch_instance(ami_id: str, key: str, type: str):
    "Create an instance on AWS with specific AMI"
    current_ami_ids = [ami.id for ami in get_amis()]
    if ami_id not in current_ami_ids:
        msg = ("Provided AMI id invalid. Use the ami-list command to check "
               "for AMIs belonging to you.")
        sys.exit(click.echo(msg))

    instance = create_instance(ami_id, key, type)
    click.echo("Instance launching, please wait..")
    inst_id = instance.id
    instance.wait_until_running()
    click.echo(f"Instance {inst_id} successfully launched.")

    click.echo("Now accessible via the command")
    public_dns = get_instance(inst_id).public_dns_name
    click.echo(f"ssh -i ~/.ssh/{key}.pem ubuntu@{public_dns}")


@instance.command('terminate')
@click.argument('instance_id', type=click.STRING)
def terminate_instance(instance_id: str):
    "Terminate an instance running on AWS"
    instance = get_instance(instance_id)

    if instance.state['Name'] != 'running':
        sys.exit("Provided instance not currently running. "
                 "Operation Aborting.")
    else:
        instance.terminate()
        click.echo(f"Instance {instance_id} now terminating.")


if __name__ == '__main__':
    cli()
