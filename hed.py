#!/usr/bin/env python

import torch
# import torch.utils.serialization

import getopt
import math
import numpy
import os
import PIL
import PIL.Image
import sys


torch.set_grad_enabled(False) # make sure to not compute gradients for computational performance


train_on_gpu = torch.cuda.is_available()


if train_on_gpu:
    torch.cuda.device(1)
    torch.backends.cudnn.enabled = True



class Network(torch.nn.Module):
	def __init__(self):
		super(Network, self).__init__()
		model_name = 'network-bsds500.pytorch'

		self.moduleVggOne = torch.nn.Sequential(
			torch.nn.Conv2d(in_channels=3, out_channels=64, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False)
		)

		self.moduleVggTwo = torch.nn.Sequential(
			torch.nn.MaxPool2d(kernel_size=2, stride=2),
			torch.nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=128, out_channels=128, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False)
		)

		self.moduleVggThr = torch.nn.Sequential(
			torch.nn.MaxPool2d(kernel_size=2, stride=2),
			torch.nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=256, out_channels=256, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=256, out_channels=256, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False)
		)

		self.moduleVggFou = torch.nn.Sequential(
			torch.nn.MaxPool2d(kernel_size=2, stride=2),
			torch.nn.Conv2d(in_channels=256, out_channels=512, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False)
		)

		self.moduleVggFiv = torch.nn.Sequential(
			torch.nn.MaxPool2d(kernel_size=2, stride=2),
			torch.nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False),
			torch.nn.Conv2d(in_channels=512, out_channels=512, kernel_size=3, stride=1, padding=1),
			torch.nn.ReLU(inplace=False)
		)

		self.moduleScoreOne = torch.nn.Conv2d(in_channels=64, out_channels=1, kernel_size=1, stride=1, padding=0)
		self.moduleScoreTwo = torch.nn.Conv2d(in_channels=128, out_channels=1, kernel_size=1, stride=1, padding=0)
		self.moduleScoreThr = torch.nn.Conv2d(in_channels=256, out_channels=1, kernel_size=1, stride=1, padding=0)
		self.moduleScoreFou = torch.nn.Conv2d(in_channels=512, out_channels=1, kernel_size=1, stride=1, padding=0)
		self.moduleScoreFiv = torch.nn.Conv2d(in_channels=512, out_channels=1, kernel_size=1, stride=1, padding=0)

		self.moduleCombine = torch.nn.Sequential(
			torch.nn.Conv2d(in_channels=5, out_channels=1, kernel_size=1, stride=1, padding=0),
			torch.nn.Sigmoid()
		)

		self.load_state_dict(torch.load(model_name))
	# end

	def forward(self, tensorInput):
		tensorBlue = (tensorInput[:, 0:1, :, :] * 255.0) - 104.00698793
		tensorGreen = (tensorInput[:, 1:2, :, :] * 255.0) - 116.66876762
		tensorRed = (tensorInput[:, 2:3, :, :] * 255.0) - 122.67891434

		tensorInput = torch.cat([ tensorBlue, tensorGreen, tensorRed ], 1)

		tensorVggOne = self.moduleVggOne(tensorInput)
		tensorVggTwo = self.moduleVggTwo(tensorVggOne)
		tensorVggThr = self.moduleVggThr(tensorVggTwo)
		tensorVggFou = self.moduleVggFou(tensorVggThr)
		tensorVggFiv = self.moduleVggFiv(tensorVggFou)

		tensorScoreOne = self.moduleScoreOne(tensorVggOne)
		tensorScoreTwo = self.moduleScoreTwo(tensorVggTwo)
		tensorScoreThr = self.moduleScoreThr(tensorVggThr)
		tensorScoreFou = self.moduleScoreFou(tensorVggFou)
		tensorScoreFiv = self.moduleScoreFiv(tensorVggFiv)

		tensorScoreOne = torch.nn.functional.interpolate(input=tensorScoreOne, size=(tensorInput.size(2), tensorInput.size(3)), mode='bilinear', align_corners=False)
		tensorScoreTwo = torch.nn.functional.interpolate(input=tensorScoreTwo, size=(tensorInput.size(2), tensorInput.size(3)), mode='bilinear', align_corners=False)
		tensorScoreThr = torch.nn.functional.interpolate(input=tensorScoreThr, size=(tensorInput.size(2), tensorInput.size(3)), mode='bilinear', align_corners=False)
		tensorScoreFou = torch.nn.functional.interpolate(input=tensorScoreFou, size=(tensorInput.size(2), tensorInput.size(3)), mode='bilinear', align_corners=False)
		tensorScoreFiv = torch.nn.functional.interpolate(input=tensorScoreFiv, size=(tensorInput.size(2), tensorInput.size(3)), mode='bilinear', align_corners=False)

		return self.moduleCombine(torch.cat([ tensorScoreOne, tensorScoreTwo, tensorScoreThr, tensorScoreFou, tensorScoreFiv ], 1))
	

def estimate(tensorInput,moduleNetwork):
	tensorOutput = torch.FloatTensor()

	intWidth = tensorInput.size(2)
	intHeight = tensorInput.size(1)

	assert(intWidth == 480) # remember that there is no guarantee for correctness, comment this line out if you acknowledge this and want to continue
	assert(intHeight == 320) # remember that there is no guarantee for correctness, comment this line out if you acknowledge this and want to continue

	if train_on_gpu:
		tensorInput = tensorInput.cuda()
		tensorOutput = tensorOutput.cuda()
	else:
		tensorInput = tensorInput.cpu()
		tensorOutput = tensorOutput.cpu()

	# end

	if True:
		tensorPreprocessed = tensorInput.view(1, 3, intHeight, intWidth)

		tensorOutput.resize_(1, intHeight, intWidth).copy_(moduleNetwork(tensorPreprocessed)[0, :, :, :])
	# end

	if True:
		tensorInput = tensorInput.cpu()
		tensorOutput = tensorOutput.cpu()
	# end

	return tensorOutput
