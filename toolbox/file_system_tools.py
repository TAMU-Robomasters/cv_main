import sys
import os
from os.path import isabs, isfile, isdir, join, dirname, basename, exists, splitext, relpath
from os import remove, getcwd, makedirs, listdir, rename, rmdir, system
from shutil import move
from pathlib import Path
import glob
import regex as re
import numpy as np
import numpy
import pickle
import random
import itertools
import time
import subprocess
from subprocess import call
import json
import cv2 as cv
import cv2
import yaml
import shutil


# 
# create a class for generate filesystem management
# 
class FileSys():
    @classmethod
    def write(self, data, to=None):
        # make sure the path exists
        FileSys.makedirs(os.path.dirname(to))
        with open(to, 'w') as the_file:
            the_file.write(str(data))
    
    @classmethod
    def read(self, filepath):
        try:
            with open(filepath,'r') as f:
                output = f.read()
        except:
            output = None
        return output    
        
    @classmethod
    def delete(self, filepath):
        if isdir(filepath):
            shutil.rmtree(filepath)
        else:
            try:
                os.remove(filepath)
            except:
                pass
    
    @classmethod
    def makedirs(self, path):
        try:
            os.makedirs(path)
        except:
            pass
        
    @classmethod
    def copy(self, from_=None, to=None, new_name="", force= True):
        if new_name == "":
            raise Exception('FileSys.copy() needs a new_name= argument:\n    FileSys.copy(from_="location", to="directory", new_name="")\nif you want the name to be the same as before do new_name=None')
        elif new_name is None:
            new_name = os.path.basename(from_)
        
        # get the full path
        to = os.path.join(to, new_name)
        # if theres a file in the target, delete it
        if force and FileSys.exists(to):
            FileSys.delete(to)
        # make sure the containing folder exists
        FileSys.makedirs(os.path.dirname(to))
        if os.path.isdir(from_):
            shutil.copytree(from_, to)
        else:
            return shutil.copy(from_, to)
    
    @classmethod
    def move(self, from_=None, to=None, new_name="", force= True):
        if new_name == "":
            raise Exception('FileSys.move() needs a new_name= argument:\n    FileSys.move(from_="location", to="directory", new_name="")\nif you want the name to be the same as before do new_name=None')
        elif new_name is None:
            new_name = os.path.basename(from_)
        
        # get the full path
        to = os.path.join(to, new_name)
        # make sure the containing folder exists
        FileSys.makedirs(os.path.dirname(to))
        shutil.move(from_, to)
    
    @classmethod
    def exists(self, *args):
        return FileSys.does_exist(*args)
    
    @classmethod
    def does_exist(self, path):
        return os.path.exists(path)
    
    @classmethod
    def is_folder(self, *args):
        return FileSys.is_directory(*args)
        
    @classmethod
    def is_dir(self, *args):
        return FileSys.is_directory(*args)
        
    @classmethod
    def is_directory(self, path):
        return os.path.isdir(path)
    
    @classmethod
    def is_file(self, path):
        return os.path.isfile(path)

    @classmethod
    def list_files(self, path="."):
        return [ x for x in FileSys.ls(path) if FileSys.is_file(x) ]
    
    @classmethod
    def list_folders(self, path="."):
        return [ x for x in FileSys.ls(path) if FileSys.is_folder(x) ]
    
    @classmethod
    def ls(self, filepath="."):
        glob_val = filepath
        if os.path.isdir(filepath):
            glob_val = os.path.join(filepath, "*")
        return glob.glob(glob_val)

    @classmethod
    def touch(self, path):
        FileSys.makedirs(FileSys.dirname(path))
        if not FileSys.exists(path):
            FileSys.write("", to=path)
    
    @classmethod
    def touch_dir(self, path):
        FileSys.makedirs(path)
    
    @classmethod
    def dirname(self, path):
        return os.path.dirname(path)
    
    @classmethod
    def basename(self, path):
        return os.path.basename(path)
    
    @classmethod
    def extname(self, path):
        filename, file_extension = os.path.splitext(path)
        return file_extension
    
    @classmethod
    def path_pieces(self, path):
        """
        example:
            *folders, file_name, file_extension = FileSys.path_pieces("/this/is/a/filepath.txt")
        """
        folders = []
        while 1:
            path, folder = os.path.split(path)

            if folder != "":
                folders.append(folder)
            else:
                if path != "":
                    folders.append(path)

                break
        folders.reverse()
        *folders, file = folders
        filename, file_extension = os.path.splitext(file)
        return [ *folders, filename, file_extension ]
    
    @classmethod
    def join(self, *paths):
        return os.path.join(*paths)
    
    @classmethod
    def absolute_path(self, path):
        return os.path.abspath(path)
    
FS = FileSys