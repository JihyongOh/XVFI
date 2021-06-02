close all;
clear;clc;
fid = fopen('./vimeo_triplet/tri_testlist.txt','r');
pred_path = './test_img_dir/XVFInet_Vimeo_exp1/epoch_00199_final_x2_S_tst1/';

gt_path = './vimeo_triplet/sequences/';
sample = fgetl(fid);
cnt = 0;

while ischar(sample)
    cnt = cnt+1;
    
    pred = imread(strcat(pred_path, sample, '/im2.png'));
    gt = imread(strcat(gt_path, sample, '/im2.png'));
    
    
    [h,w,c] = size(pred);
    
    pred_y = pred;
    gt_y = gt;
    
    total_psnr1(cnt) = psnr(pred, gt);
    total_ssim1(cnt) = ssim(pred_y, gt_y);
    fprintf('%s : %f, %f \n', sample, total_psnr1(cnt), total_ssim1(cnt))  
    
    sample = fgetl(fid);
end
cnt
mean(total_psnr1)
mean(total_ssim1)
