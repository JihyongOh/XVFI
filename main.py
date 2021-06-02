import argparse, os, shutil, time, random, torch, cv2, datetime, torch.utils.data, math
import torch.backends.cudnn as cudnn
import torch.optim as optim
import numpy as np

from torch.autograd import Variable
from utils import *
from XVFInet import *
from collections import Counter

def parse_args():
	desc = "PyTorch implementation for XVFI"
	parser = argparse.ArgumentParser(description=desc)

	parser.add_argument('--gpu', type=int, default=0, help='gpu index')
	parser.add_argument('--net_type', type=str, default='XVFInet', choices=['XVFInet'], help='The type of Net')
	parser.add_argument('--net_object', default=XVFInet, choices=[XVFInet], help='The type of Net')
	parser.add_argument('--exp_num', type=int, default=1, help='The experiment number')
	parser.add_argument('--phase', type=str, default='train', choices=['train', 'test', 'metrics_evaluation'])
	parser.add_argument('--continue_training', action='store_true', default=False, help='continue the training')

	""" Information of directories """
	parser.add_argument('--test_img_dir', type=str, default='./test_img_dir', help='test_img_dir path')
	parser.add_argument('--text_dir', type=str, default='./text_dir', help='text_dir path')
	parser.add_argument('--checkpoint_dir', type=str, default='./checkpoint_dir', help='checkpoint_dir')
	parser.add_argument('--log_dir', type=str, default='./log_dir', help='Directory name to save training logs')

	parser.add_argument('--dataset', default='X4K1000FPS', choices=['X4K1000FPS','Vimeo'], help='Training/test Dataset')
	
	# parser.add_argument('--train_data_path', type=str, default='./X4K1000FPS/train')
	# parser.add_argument('--val_data_path', type=str, default='./X4K1000FPS/val')
	# parser.add_argument('--test_data_path', type=str, default='./X4K1000FPS/test')

	parser.add_argument('--train_data_path', type=str, default='../Datasets/VIC_4K_1000FPS/train')
	parser.add_argument('--val_data_path', type=str, default='../Datasets/VIC_4K_1000FPS/val')
	parser.add_argument('--test_data_path', type=str, default='../Datasets/VIC_4K_1000FPS/test')
	

	# parser.add_argument('--vimeo_data_path', type=str, default='./vimeo_triplet')
	parser.add_argument('--vimeo_data_path', type=str, default='../Datasets/vimeo_triplet/')

	""" Hyperparameters for Training (when [phase=='train']) """
	parser.add_argument('--epochs', type=int, default=200, help='The number of epochs to run')
	parser.add_argument('--freq_display', type=int, default=100, help='The number of iterations frequency for display')
	parser.add_argument('--save_img_num', type=int, default=4, help='The number of saved image while training for visualization. It should smaller than the batch_size')
	parser.add_argument('--init_lr', type=float, default=1e-4, help='The initial learning rate')
	parser.add_argument('--lr_dec_fac', type=float, default=0.25, help='step - lr_decreasing_factor') 
	parser.add_argument('--lr_milestones', type=int, default=[100, 150, 180]) 
	parser.add_argument('--lr_dec_start', type=int, default=0, help='When scheduler is StepLR, lr decreases from epoch at lr_dec_start') 
	parser.add_argument('--batch_size', type=int, default=8, help='The size of batch size.')
	parser.add_argument('--weight_decay', type=float, default=0, help='for optim., weight decay (default: 0)')

	parser.add_argument('--need_patch', default=True, help='get patch form image')
	parser.add_argument('--img_ch', type=int, default=3, help='base number of channels for image')
	parser.add_argument('--nf', type=int, default=64, help='base number of channels for feature maps') # 64
	parser.add_argument('--module_scale_factor', type=int, default=4, help='sptial reduction for pixelshuffle')
	parser.add_argument('--patch_size', type=int, default=384, help='patch size')
	parser.add_argument('--num_thrds', type=int, default=4, help='number of threads for data loading') #check
	parser.add_argument('--loss_type', default='L1', choices=['L1','MSE','L1_Charbonnier_loss'], help='Loss type')

	parser.add_argument('--S_trn', type=int, default=3, help='The lowest scale depth for training') 
	parser.add_argument('--S_tst', type=int, default=5, help='The lowest scale depth for test') 


	""" Weighting Parameters Lambda for Losses (when [phase=='train']) """
	parser.add_argument('--rec_lambda', type=float, default=1.0, help='Lambda for Reconstruction Loss')

	""" Settings for Testing (when [phase=='test']) """
	parser.add_argument('--saving_flow_flag', default=False)
	parser.add_argument('--multiple', type=int, default=8, choices=[4, 8, 16, 32])
	parser.add_argument('--metrics_types', type=list, default=["PSNR", "SSIM", "tOF"], choices=["PSNR", "SSIM", "tOF"])

	return check_args(parser.parse_args())


def check_args(args):
	# --checkpoint_dir
	check_folder(args.checkpoint_dir)

	# --text_dir
	check_folder(args.text_dir)

	# --log_dir
	check_folder(args.log_dir)

	# --test_img_dir
	check_folder(args.test_img_dir)

	return args


def main():
	args = parse_args()
	if args.dataset == 'Vimeo':
		args.multiple = 2
		args.S_trn = 1
		args.S_tst = 1
		args.module_scale_factor = 2
		args.patch_size = 256
		args.batch_size = 16
		print('vimeo triplet data dir : ', args.vimeo_data_path)

	print("Exp:", args.exp_num)
	args.model_dir = args.net_type + '_' + args.dataset + '_exp' + str(args.exp_num)  # ex) model_dir = "XVFInet_X4K1000FPS_exp1"

	if args is None:
		exit()
	for arg in vars(args):
		print('# {} : {}'.format(arg, getattr(args, arg)))
	device = torch.device('cuda:' + str(args.gpu) if torch.cuda.is_available() else 'cpu')  # will be used as "x.to(device)"
	torch.cuda.set_device(device)  # change allocation of current GPU
	# caution!!!! if not "torch.cuda.set_device()":
	# RuntimeError: grid_sampler(): expected input and grid to be on same device, but input is on cuda:1 and grid is on cuda:0
	print('Available devices: ', torch.cuda.device_count())
	print('Current cuda device: ', torch.cuda.current_device())
	print('Current cuda device name: ', torch.cuda.get_device_name(device))
	if args.gpu is not None:
		print("Use GPU: {} is used".format(args.gpu))

	
	SM = save_manager(args)

	""" Initialize a model """
	model_net = args.net_object(args).apply(weights_init).to(device)
	criterion = [set_rec_loss(args).to(device), set_smoothness_loss().to(device)]
	
	# to enable the inbuilt cudnn auto-tuner
	# to find the best algorithm to use for your hardware.
	cudnn.benchmark = True

	if args.phase == "train":
		train(model_net, criterion, device, SM, args)
		epoch = args.epochs - 1

	elif args.phase == "test" or args.phase == "metrics_evaluation":
		checkpoint = SM.load_model()
		model_net.load_state_dict(checkpoint['state_dict_Model'])
		epoch = checkpoint['last_epoch']

	postfix = '_final_x' + str(args.multiple) + '_S_tst' + str(args.S_tst)
	if args.phase != "metrics_evaluation":
		print("\n-------------------------------------- Final Test starts -------------------------------------- ")
		print('Evaluate on test set (final test) with multiple = %d '% (args.multiple))

		final_test_loader = get_test_data(args, multiple=args.multiple, validation=False) # multiple is only used for X4K1000FPS

		testLoss, testPSNR, testSSIM, final_pred_save_path = test(final_test_loader, model_net,
																  criterion, epoch,
																  args, device,
																  multiple=args.multiple,
																  postfix=postfix, validation= False)
		SM.write_info('Final 4k frames PSNR : {:.4}\n'.format(testPSNR))

	if args.dataset == 'X4K1000FPS':
		final_pred_save_path = os.path.join(args.test_img_dir, args.model_dir, 'epoch_' + str(epoch).zfill(5)) + postfix
		metrics_evaluation_X_Test(final_pred_save_path, args.test_data_path, args.metrics_types, flow_flag=args.saving_flow_flag, multiple=args.multiple) 
	print("------------------------- Test has been ended. -------------------------\n")
	print("Exp:", args.exp_num)
	

def train(model_net, criterion, device, save_manager, args):
	SM = save_manager
	multi_scale_recon_loss = criterion[0] 
	smoothness_loss = criterion[1]

	optimizer = optim.Adam(model_net.parameters(), lr=args.init_lr,betas=(0.9, 0.999), weight_decay=args.weight_decay)  # optimizer
	scheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=args.lr_milestones, gamma=args.lr_dec_fac) 

	last_epoch = 0
	best_PSNR = 0.0
	
	if args.continue_training:
		checkpoint = SM.load_model()
		last_epoch = checkpoint['last_epoch'] + 1
		best_PSNR = checkpoint['best_PSNR']
		model_net.load_state_dict(checkpoint['state_dict_Model'])
		optimizer.load_state_dict(checkpoint['state_dict_Optimizer'])
		scheduler.load_state_dict(checkpoint['state_dict_Scheduler'])
		print("Optimizer and Scheduler have been reloaded. ")
	scheduler.milestones = Counter(args.lr_milestones)
	scheduler.gamma = args.lr_dec_fac
	print("scheduler.milestones : {}, scheduler.gamma : {}".format(scheduler.milestones, scheduler.gamma))
	start_epoch = last_epoch

	# switch to train mode
	model_net.train()

	start_time = time.time()

	SM.write_info('Epoch\ttrainLoss\ttestPSNR\tbest_PSNR\n')
	print("[*] Training starts")

	# Main training loop for total epochs (start from 'epoch=0')
	valid_loader = get_test_data(args, multiple=4, validation=True)  # multiple is only used for X4K1000FPS

	for epoch in range(start_epoch, args.epochs):
		train_loader = get_train_data(args, max_t_step_size=32) # max_t_step_size (temporal distance) is only used for X4K1000FPS

		batch_time = AverageClass('batch_time[s]:', ':6.3f')
		losses = AverageClass('Loss:', ':.4e')
		progress = ProgressMeter(len(train_loader), batch_time, losses, prefix="Epoch: [{}]".format(epoch))

		print('Start epoch {} at [{:s}], learning rate : [{}]'.format(epoch, (str(datetime.now())[:-7]),optimizer.param_groups[0]['lr']))

		# train for one epoch
		for trainIndex, (frames, t_value) in enumerate(train_loader):

			input_frames = frames[:, :, :-1, :]  # [B, C, T, H, W]
			frameT = frames[:, :, -1, :]  # [B, C, H, W]

			# Getting the input and the target from the training set
			input_frames = Variable(input_frames.to(device))
			frameT = Variable(frameT.to(device))  # ground truth for frameT
			t_value = Variable(t_value.to(device))  # [B,1]

			optimizer.zero_grad()
			# compute output
			pred_frameT_pyramid, pred_flow_pyramid, occ_map, simple_mean = model_net(input_frames, t_value)
			rec_loss = 0.0
			smooth_loss = 0.0
			for l, pred_frameT_l in enumerate(pred_frameT_pyramid):
				rec_loss += args.rec_lambda * multi_scale_recon_loss(pred_frameT_l, F.interpolate(frameT, scale_factor=1 / (2 ** l),mode='bicubic',align_corners=False))
			smooth_loss += 0.5 * smoothness_loss(pred_flow_pyramid[0], F.interpolate(frameT, scale_factor=1/args.module_scale_factor, mode='bicubic', align_corners=False)) # Apply 1st order edge-aware smoothness loss to the fineset level
			rec_loss /= len(pred_frameT_pyramid)
			pred_frameT = pred_frameT_pyramid[0] # final result I^0_t at original scale (s=0)
			pred_coarse_flow = 2**(args.S_trn) * F.interpolate(pred_flow_pyramid[-1], scale_factor=2 ** (args.S_trn)*args.module_scale_factor, mode='bicubic', align_corners=False) 
			pred_fine_flow = F.interpolate(pred_flow_pyramid[0], scale_factor=args.module_scale_factor, mode='bicubic', align_corners=False) 

			total_loss = rec_loss + smooth_loss

			# compute gradient and do SGD step
			total_loss.backward()  # Backpropagate
			optimizer.step()  # Optimizer update

			# measure accumulated time and update average "batch" time consumptions via "AverageClass"
			# update average values via "AverageClass"
			losses.update(total_loss.item(), 1)
			batch_time.update(time.time() - start_time)
			start_time = time.time()

			if trainIndex % args.freq_display == 0:
				progress.print(trainIndex)
				batch_images = get_batch_images(args, save_img_num=args.save_img_num, save_images=[pred_frameT, pred_coarse_flow, pred_fine_flow, frameT, simple_mean, occ_map]) 
				cv2.imwrite('./log_dir/{:03d}_{:04d}_training.png'.format(epoch,trainIndex), batch_images)

		if epoch >= args.lr_dec_start:
			scheduler.step()

		# if (epoch + 1) % 10 == 0 or epoch==0:
		val_multiple = 4 if args.dataset == 'X4K1000FPS' else 2 
		print('\nEvaluate on test set (validation while training) with multiple = {}'.format(val_multiple))
		postfix = '_val_'+ str(val_multiple) +'_S_tst' + str(args.S_tst)
		testLoss, testPSNR, testSSIM, final_pred_save_path = test(valid_loader, model_net, criterion, epoch, args, device, multiple=val_multiple, postfix=postfix, validation= True)

		# remember best best_PSNR and best_SSIM and save checkpoint
		print("best_PSNR : {:.3f}, testPSNR : {:.3f}".format(best_PSNR, testPSNR))
		best_PSNR_flag = testPSNR > best_PSNR
		best_PSNR = max(testPSNR, best_PSNR)
		# save checkpoint.
		combined_state_dict = {
			'net_type': args.net_type,
			'last_epoch': epoch,
			'batch_size': args.batch_size,
			'trainLoss': losses.avg,
			'testLoss': testLoss,
			'testPSNR': testPSNR,
			'best_PSNR': best_PSNR,
			'state_dict_Model': model_net.state_dict(),
			'state_dict_Optimizer': optimizer.state_dict(),
			'state_dict_Scheduler': scheduler.state_dict()}

		SM.save_best_model(combined_state_dict, best_PSNR_flag)

		if (epoch + 1) % 10 ==0:
			SM.save_epc_model(combined_state_dict, epoch)
		SM.write_info('{}\t{:.4}\t{:.4}\t{:.4}\n'.format(epoch, losses.avg, testPSNR, best_PSNR))

	print("------------------------- Training has been ended. -------------------------\n")
	print("information of model:", args.model_dir)
	print("best_PSNR of model:", best_PSNR)


def test(test_loader, model_net, criterion, epoch, args, device, multiple, postfix, validation):
	batch_time = AverageClass('Time:', ':6.3f')
	losses = AverageClass('testLoss:', ':.4e')
	PSNRs = AverageClass('testPSNR:', ':.4e')
	SSIMs = AverageClass('testSSIM:', ':.4e')

	# progress = ProgressMeter(len(test_loader), batch_time, accm_time, losses, PSNRs, SSIMs, prefix='Test after Epoch[{}]: '.format(epoch))
	progress = ProgressMeter(len(test_loader), PSNRs, SSIMs, prefix='Test after Epoch[{}]: '.format(epoch))

	multi_scale_recon_loss = criterion[0]

	# switch to evaluate mode
	model_net.eval()

	print("------------------------------------------- Test ----------------------------------------------")
	with torch.no_grad():
		start_time = time.time()
		for testIndex, (frames, t_value, scene_name, frameRange) in enumerate(test_loader):
			# Shape of 'frames' : [1,C,T+1,H,W]
			frameT = frames[:, :, -1, :, :]  # [1,C,H,W]
			It_Path, I0_Path, I1_Path = frameRange
			
			frameT = Variable(frameT.to(device))  # ground truth for frameT
			t_value = Variable(t_value.to(device))

			if (testIndex % (multiple - 1)) == 0:
				input_frames = frames[:, :, :-1, :, :]  # [1,C,T,H,W]
				input_frames = Variable(input_frames.to(device))

			
			pred_frameT = model_net(input_frames, t_value, is_training=False) 

			if args.dataset == 'X4K1000FPS' and not validation :
				""" Belows makes the input's spatial resolution to be multiple of 2^n. """
				if args.S_tst == 3:
					padding = 16
				elif args.S_tst == 4:
					padding = 112
				elif args.S_tst == 5:
					padding = 400
				pred_frameT = pred_frameT[:,:,:-padding,:]
				frameT = frameT[:,:,:-padding,:]

			test_loss = args.rec_lambda * multi_scale_recon_loss(pred_frameT, frameT)

			pred_frameT = np.squeeze(pred_frameT.detach().cpu().numpy())
			frameT = np.squeeze(frameT.detach().cpu().numpy())

			""" compute PSNR & SSIM """
			output_img = np.around(denorm255_np(np.transpose(pred_frameT, [1, 2, 0])))  # [h,w,c] and [-1,1] to [0,255]
			target_img = denorm255_np(np.transpose(frameT, [1, 2, 0]))  # [h,w,c] and [-1,1] to [0,255]

			test_psnr = psnr(target_img, output_img)  
			test_ssim = ssim_bgr(target_img, output_img)  ############### CAUTION: calculation for BGR

			""" save frame0 & frame1 """
			if validation:
				epoch_save_path = os.path.join(args.test_img_dir, args.model_dir, 'latest' + postfix)
			else:
				epoch_save_path = os.path.join(args.test_img_dir, args.model_dir, 'epoch_' + str(epoch).zfill(5) + postfix)
			check_folder(epoch_save_path)
			scene_save_path = os.path.join(epoch_save_path, scene_name[0])
			check_folder(scene_save_path)
			
			if (testIndex % (multiple - 1)) == 0:
				if args.dataset == 'X4K1000FPS' and not validation :
					save_input_frames = frames[:, :, :-1, :-padding, :]
				else:
					save_input_frames = frames[:, :, :-1, :, :]
				cv2.imwrite(scene_save_path + '/' + I0_Path[0], np.transpose(np.squeeze(denorm255_np(save_input_frames[:, :, 0, :, :].detach().numpy())), [1, 2, 0]).astype(np.uint8))
				cv2.imwrite(scene_save_path + '/' + I1_Path[0], np.transpose(np.squeeze(denorm255_np(save_input_frames[:, :, 1, :, :].detach().numpy())), [1, 2, 0]).astype(np.uint8))

			cv2.imwrite(scene_save_path + '/' + It_Path[0], output_img.astype(np.uint8))

			# measure
			losses.update(test_loss.item(), 1)
			PSNRs.update(test_psnr, 1)
			SSIMs.update(test_ssim, 1)

			# measure elapsed time
			batch_time.update(time.time() - start_time)
			start_time = time.time()

			if (testIndex % (multiple - 1)) == multiple - 2:
				progress.print(testIndex)
				
		print("-----------------------------------------------------------------------------------------------")

	return losses.avg, PSNRs.avg, SSIMs.avg, epoch_save_path


if __name__ == '__main__':
	main()