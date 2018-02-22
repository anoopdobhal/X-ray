"""
This file contains tools for loading and transforming data for use by PyTorch models.

Tutorial on data loading: http://pytorch.org/tutorials/beginner/data_loading_tutorial.html
"""
import random
import os
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

# Statistics from ImageNet dataset, to which we normalize our X-ray images
normalize = transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225])

# Define an object that transforms a given training set example
train_transformer = transforms.Compose([
    transforms.RandomHorizontalFlip(),  # Randomly flip image horizontally
    transforms.ToTensor(),              # Transform into a Torch tensor
    normalize                           # Normalize
])

# Define an object that transforms a given evaluation (i.e. validation or test) set example
# Note that we do not flip inputs during evaluation
eval_transformer = transforms.Compose([
    transforms.ToTensor(),  # Transform into a Torch tensor
    normalize               # Normalize
])


class ChestXRayDataset(Dataset):
    """
    A standard PyTorch definition of Dataset which defines the functions __len__ and __getitem__.
    """
    def __init__(self, data_dir, image_list_file, transform):
        """
        Stores the filenames of the images in this dataset, and which transforms to apply on them.

        Arguments:
            data_dir: (string) directory containing the dataset
            image_list_file: (string) name of the file containing a list of image names and their labels
            transform: (torchvision.transforms) transformation to apply on each image
        """
        image_names = []
        labels = []
        with open(image_list_file, "r") as f:
            for line in f:
                items = line.split()
                image_name = items[0]
                image_name = os.path.join(data_dir, image_name)
                image_names.append(image_name)
                label = items[1:]
                label = [int(i) for i in label]
                labels.append(label)

        self.image_names = image_names
        self.labels = labels
        self.transform = transform

    def __len__(self):
        """
        Returns the size of the dataset.
        """
        return len(self.image_names)

    def __getitem__(self, idx):
        """
        Returns the image at index 'idx' (with transform applied), and its labels, from the dataset.

        Args:
            idx: (int) index in [0, 1, ..., size_of_dataset-1]

        Returns:
            image: (Tensor) transformed image
            labels: (Tensor) corresponding labels of image
        """
        image = Image.open(self.image_names[idx]).convert('RGB')  # PIL image
        if self.transform is not None:
            image = self.transform(image)
        return image, torch.FloatTensor(self.labels[idx])


def fetch_dataloader(types, data_dir, params, small=None):
    """
    Returns DataLoaders containing train, val, and/or test data from a given directory.

    Args:
        types: (list) a subset of the list ['train', 'val', 'test'] indicating which parts of dataset are desired
        data_dir: (string) name of directory containing the dataset
        params: (Params) hyperparameters object

    Returns:
        data: (dict) a map from (a type in types) --> (a DataLoader object containing that data type)
    """
    dataloaders = {}

    for split in ['train', 'val', 'test']:
        if split in types:
            image_file = os.path.join(data_dir, "..")

            # Obtain a list of images belonging to this split            
            if small is None:
                labels_dir = "../labels/{}_list.txt".format(split)    
            else:
                labels_dir = "../labels/small_{}_list.txt".format(split)
            image_list_file = os.path.join(data_dir, labels_dir)
            
            # Training set and val/test tests use different transforms and shuffling
            if split == 'train':
                transform = train_transformer
                shuffle = True
            else:
                transform = eval_transformer
                shuffle = False

            dataset = ChestXRayDataset(data_dir=data_dir,
                                       image_list_file=image_list_file,
                                       transform=eval_transformer)

            dataloader = DataLoader(dataset=dataset, 
                                    batch_size=params.batch_size, shuffle=shuffle,
                                    num_workers=params.num_workers,
                                    pin_memory=params.cuda)

            dataloaders[split] = dataloader

    return dataloaders
