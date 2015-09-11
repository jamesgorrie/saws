# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
import os
import re
import subprocess
from enum import Enum
from .commands import SOURCES_DIR


class AwsResources(object):

    def __init__(self,
                 refresh_instance_ids=True,
                 refresh_instance_tags=True,
                 refresh_bucket_names=True):
        self.instance_ids = []
        self.instance_tag_keys = set()
        self.instance_tag_values = set()
        self.bucket_names = []
        self.refresh_instance_ids = refresh_instance_ids
        self.refresh_instance_tags = refresh_instance_tags
        self.refresh_bucket_names = refresh_bucket_names
        self.instance_ids_marker = '[instance ids]'
        self.instance_tag_keys_marker = '[instance tag keys]'
        self.instance_tag_values_marker = '[instance tag values]'
        self.bucket_names_marker = '[bucket names]'

    def refresh(self, force_refresh=False):
        """
        Refreshes the AWS resources
        :return: None
        """
        p = SOURCES_DIR
        f = os.path.join(p, 'data/RESOURCES.txt')
        if not force_refresh:
            try:
                self.refresh_resources_from_file(f, p)
                print('Loaded resources from cache')
            except IOError:
                print('No resource cache found')
                force_refresh = True
        if force_refresh:
            print('Refreshing resources...')
            if self.refresh_instance_ids:
                print('  Refreshing instance ids...')
                self.query_instance_ids()
            if self.refresh_instance_tags:
                print('  Refreshing instance tags...')
                self.query_instance_tag_keys()
                self.query_instance_tag_values()
            if self.refresh_bucket_names:
                print('  Refreshing bucket names...')
                self.query_bucket_names()
            print('Done refreshing')
        try:
            self.save_resources_to_file(f, p)
        except IOError as e:
            print(e)

    def query_instance_ids(self):
        command = 'aws ec2 describe-instances --query "Reservations[].Instances[].[InstanceId]" --output text'
        try:
            result = subprocess.check_output(command, shell=True)
            result = re.sub('\n', ' ', result)
            self.instance_ids = result.split()
        except Exception as e:
            print(e)

    def query_instance_tag_keys(self):
        command = 'aws ec2 describe-instances --filters "Name=tag-key,Values=*" --query Reservations[].Instances[].Tags[].Key --output text'
        try:
            result = subprocess.check_output(command, shell=True)
            self.instance_tag_keys = set(result.split('\t'))
        except Exception as e:
            print(e)

    def query_instance_tag_values(self):
        command = 'aws ec2 describe-instances --filters "Name=tag-value,Values=*" --query Reservations[].Instances[].Tags[].Value --output text'
        try:
            result = subprocess.check_output(command, shell=True)
            self.instance_tag_values = set(result.split('\t'))
        except Exception as e:
            print(e)

    def query_bucket_names(self):
        command = 'aws s3 ls'
        try:
            output = subprocess.check_output(command, shell=True)
            result_list = output.split('\n')
            for result in result_list:
                try:
                    result = result.split()[-1]
                    self.bucket_names.append(result)
                except:
                    # Ignore blank lines
                    pass
        except Exception as e:
            print(e)

    def refresh_resources_from_file(self, f, p):
        class ResType(Enum):

            INSTANCE_IDS, INSTANCE_TAG_KEYS, INSTANCE_TAG_VALUES, \
                BUCKET_NAMES = range(4)

        res_type = ResType.INSTANCE_IDS
        with open(f) as fp:
            self.instance_ids = []
            self.instance_tag_keys = set()
            self.instance_tag_values = set()
            self.bucket_names = []
            instance_tag_keys_list = []
            instance_tag_values_list = []
            for line in fp:
                line = re.sub('\n', '', line)
                if line.strip() == '':
                    continue
                elif self.instance_ids_marker in line:
                    res_type = ResType.INSTANCE_IDS
                    continue
                elif self.instance_tag_keys_marker in line:
                    res_type = ResType.INSTANCE_TAG_KEYS
                    continue
                elif self.instance_tag_values_marker in line:
                    res_type = ResType.INSTANCE_TAG_VALUES
                    continue
                elif self.bucket_names_marker in line:
                    res_type = ResType.BUCKET_NAMES
                    continue
                if res_type == ResType.INSTANCE_IDS:
                    self.instance_ids.append(line)
                elif res_type == ResType.INSTANCE_TAG_KEYS:
                    instance_tag_keys_list.append(line)
                elif res_type == ResType.INSTANCE_TAG_VALUES:
                    instance_tag_values_list.append(line)
                elif res_type == ResType.BUCKET_NAMES:
                    self.bucket_names.append(line)
            self.instance_tag_keys = set(instance_tag_keys_list)
            self.instance_tag_values = set(instance_tag_values_list)

    def save_resources_to_file(self, f, p):
        with open(f, 'w') as fp:
            fp.write(self.instance_ids_marker + '\n')
            for instance_id in self.instance_ids:
                fp.write(instance_id + '\n')
            fp.write(self.instance_tag_keys_marker + '\n')
            for instance_tag_key in self.instance_tag_keys:
                fp.write(instance_tag_key + '\n')
            fp.write(self.instance_tag_values_marker + '\n')
            for instance_tag_value in self.instance_tag_values:
                fp.write(instance_tag_value + '\n')
            fp.write(self.bucket_names_marker + '\n')
            for bucket_name in self.bucket_names:
                fp.write(bucket_name + '\n')