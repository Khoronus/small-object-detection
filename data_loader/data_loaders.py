import torch
import numpy as np

from constants import *
from base import BaseDataLoader
from utils import joint_transforms as t
from data_loader.datasets import ModVOCDetection


class JointTransformer(object):
    """ Custom transformer to jointly operate on an image and its
        corresponding bounding boxes and labels.

        The important steps are:
            Convert bounding box pixels to percent coordinates,
            Resize to specific image size (i.e. 300x300),
            Mean subtract,
            Convert image to tensor
    """
    def __init__(self, image_size, training, augment):
        self.image_size = image_size
        self.training = training
        self.augment = augment

    def __call__(self, image, boxes, labels):
        if self.augment and self.training:
            transformer = t.Compose([
                t.ConvertFromPIL(),
                t.PhotometricDistort(),
                t.Expand(IMAGENET_MEAN),
                t.RandomSampleCrop(),
                t.RandomMirror(),
                t.ToPercentCoords(),
                t.Resize(self.image_size),
                t.Normalize(IMAGENET_MEAN, IMAGENET_STD),
                t.ToTensor()
            ])
        else:
            transformer = t.Compose([
                t.ConvertFromPIL(),
                t.ToPercentCoords(),
                t.Resize(self.image_size),
                t.Normalize(IMAGENET_MEAN, IMAGENET_STD),
                t.ToTensor()
            ])
        return transformer(image, boxes, labels)


def collate_fn(batch):
    """ Collate objects together in a batch.

    Used by the dataloader for generating batches of data. This is a
    simple modification of the default collate_fn.

    Inputs:
        batch: an iterable of N sets from __getitem__()

    Return:
        a tensor of images, list of varying-size tensors of bounding boxes,
        and list of vary-size tensors of encoded labels.
    """
    images = []
    boxes_list = []
    labels_list = []

    for item in batch:
        images.append(item[0])
        boxes_list.append(item[1])
        labels_list.append(item[2])

    images = torch.stack(images, dim=0)

    return images, boxes_list, labels_list


class VOCDataLoader(BaseDataLoader):
    """
    Load Pascal VOC using BaseDataLoader
    """
    def __init__(self, data_dir, voc_params, image_size, batch_size,
                 shuffle=True, validation_split=0.0, collate_fn=collate_fn,
                 num_workers=1, augment=False, training=True):

        self.data_dir = data_dir
        self.dataset = ModVOCDetection(
            self.data_dir,
            year=voc_params['year'],
            image_set=voc_params['image_set'],
            download=False,
            joint_transform=JointTransformer(image_size,
                                             training,
                                             augment)
        )

        super(VOCDataLoader, self).__init__(self.dataset, batch_size,
                                            shuffle, validation_split,
                                            num_workers, collate_fn)
