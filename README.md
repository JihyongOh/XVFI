# XVFI
**This is the official repository of XVFI (eXtreme Video Frame Interpolation), https://arxiv.org/abs/2103.16206**

## X4K1000FPS
#### Dataset of high-resolution, high-fps video frames with extreme motion
![003](/figures/003.gif "003") ![004](/figures/004.gif "004") ![045](/figures/045.gif "045")
![078](/figures/078.gif "078") ![081](/figures/081.gif "081") ![146](/figures/146.gif "146")\
<Some examples of X4K1000FPS dataset, which are frames of 1000-fps and 4K-resolution. Our dataset contains the various scenes with extreme motions. (Displayed in spatiotemporally subsampled .gif files)>

We provide our X4K1000FPS dataset which consists of X-TEST and X-TRAIN. Please refer to our main/suppl. [paper](https://arxiv.org/abs/2103.16206) for the details of the dataset. You can download the dataset from this dropbox [link](https://www.dropbox.com/sh/duisote638etlv2/AABJw5Vygk94AWjGM4Se0Goza?dl=0).

`X-TEST` consists of 15 video clips with 33-length of 4K-1000fps frames. It follows the below directory format:
```
├──── YOUR_DIR/
    ├──── test/
       ├──── Type1/
          ├──── TEST01/
             ├──── 0000.png
             ├──── ...
             └──── 0032.png
          ├──── TEST02/
             ├──── 0000.png
             ├──── ...
             └──── 0032.png
          ├──── ...
       ├──── ...
```

`X-TRAIN` consists of 4,408 clips from various types of 110 scenes. The clips are 65-length of 1000fps frames. Each frame is the size of 768x768 cropped from 4K frame. It follows the below directory format:
```
├──── YOUR_DIR/
    ├──── train/
       ├──── 002/
          ├──── occ008.320/
             ├──── 0000.png
             ├──── ...
             └──── 0064.png
          ├──── occ008.322/
             ├──── 0000.png
             ├──── ...
             └──── 0064.png
          ├──── ...
       ├──── ...
```

After downloading the files from the link, decompress the `encoded_test.tar.gz` and `encoded_train.tar.gz`. The resulting .mp4 files can be decoded into .png files via running `mp4_decoding.py`. Please follow the instruction written in `mp4_decoding.py`.

## Coming Soon

We will provide the training and test code along with the trained weights for XVFI. 
If you find this repository useful, please consider citing our [paper](https://arxiv.org/abs/2103.16206).

## Contact
Please send me an email, flhy5836@kaist.ac.kr, jhoh94@kaist.ac.kr

**Reference**:  
> Hyeonjun Sim*, Jihyong Oh*, and Munchurl Kim "XVFI: eXtreme Video Frame Interpolation", https://arxiv.org/abs/2103.16206, 2021. (* *equal contribution*)
> 
**BibTeX**
```bibtex
@article{sim2021xvfi,
  title={XVFI: eXtreme Video Frame Interpolation},
  author={Sim, Hyeonjun and Oh, Jihyong and Kim, Munchurl},
  journal={arXiv preprint arXiv:2103.16206},
  year={2021}
}
```
