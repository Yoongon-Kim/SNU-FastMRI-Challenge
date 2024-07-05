import h5py
import random
from utils.data.transforms import DataTransform
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import numpy as np
import time
class SliceData(Dataset):
    def __init__(self, root, transform, input_key, target_key, forward=False):
        self.transform = transform
        self.input_key = input_key
        self.target_key = target_key
        self.forward = forward
        self.image_examples = []
        self.kspace_examples = []

        if not forward:
            image_files = list(Path(root / "image").iterdir())

            """
            for fname in sorted(image_files):
                num_slices = self._get_metadata(fname)

                self.image_examples += [
                    (fname, slice_ind) for slice_ind in range(num_slices)
                ]
            """
            # train data의 image_examples는 txt파일에서 가지고 오도록 함(google colab용)
            files_num = len(image_files)
            if files_num==51:
                # val data인 경우 원래처럼 image_examples 가지고 오기
                for fname in sorted(image_files):
                    num_slices = self._get_metadata(fname)

                    self.image_examples += [
                        (fname, slice_ind) for slice_ind in range(num_slices)
                    ]
            else:
                self.image_examples = self._get_metadata2('image')

        kspace_files = list(Path(root / "kspace").iterdir())

        """
            for fname in sorted(kspace_files):
                num_slices = self._get_metadata(fname)

                self.kspace_examples += [
                    (fname, slice_ind) for slice_ind in range(num_slices)
                ]
            """

        # train data의 kspace_examples는 txt파일에서 가지고 오도록 함(google colab용)
        files_num = len(kspace_files)
        if files_num==51:
            # val data인 경우 원래처럼 kspace_examples 가지고 오기
            for fname in sorted(kspace_files):
                num_slices = self._get_metadata(fname)

                self.kspace_examples += [
                    (fname, slice_ind) for slice_ind in range(num_slices)
                ]
        else:
            self.kspace_examples = self._get_metadata2('kspace')


    def _get_metadata(self, fname):
        with h5py.File(fname, "r") as hf:
            if self.input_key in hf.keys():
                num_slices = hf[self.input_key].shape[0]
            elif self.target_key in hf.keys():
                num_slices = hf[self.target_key].shape[0]
        return num_slices

    def _get_metadata2(self, data_type):
        examples = []
        if data_type == 'image':
            with open("/content/drive/MyDrive/Data/train_image_examples.txt", "r") as f:
                image_examples = f.read()
                for line in image_examples.split('\n'):
                    fname, dataslice = line.split()
                    examples.append(tuple((Path(fname), int(dataslice))))
        elif data_type == 'kspace':
            with open("/content/drive/MyDrive/Data/train_kspace_examples.txt", "r") as f:
                kspace_examples = f.read()
                for line in kspace_examples.split('\n'):
                    fname, dataslice = line.split()
                    examples.append(tuple((Path(fname), int(dataslice))))
        return examples

    def __len__(self):
        return len(self.kspace_examples)

    def __getitem__(self, i):
        if not self.forward:
            image_fname, _ = self.image_examples[i]
        kspace_fname, dataslice = self.kspace_examples[i]

        with h5py.File(kspace_fname, "r") as hf:
            input = hf[self.input_key][dataslice]
            mask =  np.array(hf["mask"])
        if self.forward:
            target = -1
            attrs = -1
        else:
            with h5py.File(image_fname, "r") as hf:
                target = hf[self.target_key][dataslice]
                attrs = dict(hf.attrs)
            
        return self.transform(mask, input, target, attrs, kspace_fname.name, dataslice)


def create_data_loaders(data_path, args, shuffle=False, isforward=False):
    if isforward == False:
        max_key_ = args.max_key
        target_key_ = args.target_key
    else:
        max_key_ = -1
        target_key_ = -1
    data_storage = SliceData(
        root=data_path,
        transform=DataTransform(isforward, max_key_),
        input_key=args.input_key,
        target_key=target_key_,
        forward = isforward
    )

    data_loader = DataLoader(
        dataset=data_storage,
        batch_size=args.batch_size,
        shuffle=shuffle,
    )
    return data_loader