import boto3
from datetime import datetime, timedelta
from terminaltables import AsciiTable
from colorama import Fore, Style
from itertools import zip_longest


ec2 = boto3.resource('ec2')
client = boto3.client('ec2')


def get_instance_name(instance):
	name = [i['Value'] for i in instance.tags if i['Key'] == 'Name']
	return name[0] if name else ''

instances_iterator = ec2.instances.filter(Filters=[
	{'Name': 'tag-key', 'Values': ['Backup', 'Backup']}])

for instance in instances_iterator:
	instance_name = get_instance_name(instance)
	instance_id = instance.id

	print('Instance #{id} with name - {name}'.format(
		id=instance_id,
		name=instance_name
	))

	create_time = datetime.now()
	description = 'backup_{instance_name}_{create_time}'
	image_name = '{instance_name}_{instance_id}'

	response = client.create_image(
		Description=description.format(
			instance_name=instance_name,
			create_time=create_time
		),
		InstanceId=instance_id,
		Name=image_name.format(
			instance_name=instance_name,
			instance_id=instance_id
		),
		NoReboot=True
	)

	print(response)


old_images, normal_images = [], []
now = datetime.now()
MAX_DAYS = 7


image_iterator = ec2.images.filter(Owners=['self'])

for image in image_iterator:
	tag, name, _date = image.description.split('_')
	date = datetime.strptime(_date.split('.')[0], '%Y-%m-%d %H:%M:%S')

	if date + timedelta(days=7) > now:
		normal_images.append((image.id, image.description))
		continue

	old_images.append((image.id, image.description))
	image.deregister()


def wrap_yellow(text):
	return '{}{}{}'.format(Fore.YELLOW, text, Style.RESET_ALL)

def wrap_green(text):
	return '{}{}{}'.format(Fore.GREEN, text, Style.RESET_ALL)

table_data = [
    [wrap_yellow('Old images'),  wrap_green('New images')],
] + [[
		wrap_yellow(old) if old else '',
	 	wrap_green(new) if new else ''
 	] for old, new in zip_longest(old_images, normal_images)]


table = AsciiTable(table_data)
print(table.table)
