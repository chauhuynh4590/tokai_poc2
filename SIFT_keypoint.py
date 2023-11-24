import cv2
import numpy as np

sift= cv2.SIFT_create()

def sift_keypoint(img1,img2):
    keypoints1, descriptors1 = sift.detectAndCompute(img1,None)
    keypoints2, descriptors2 = sift.detectAndCompute(img2,None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params,search_params)
    matches = flann.knnMatch(descriptors1,descriptors2,k=2)

    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)

    result = cv2.drawMatches(img1,keypoints1,img2,keypoints2,good[:100],None,flags=2)

    # Show result
    # cv2.imshow('Matches', result)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return(len(good))


img1 = cv2.imread('C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images1/0a.png',0) 
# img2 = cv2.imread('C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images2/1b.png',0)
img2 = cv2.imread('C:/Users/ht_thien/Desktop/TOkairikaa/github/tokai_poc3/data/images2/0b.png',0)

# resize để chạy nhanh
h,w=img1.shape[:2]
img1=cv2.resize(img1,(int(w/5),int(h/5)))

h,w=img2.shape[:2]
img2=cv2.resize(img2,(int(w/5),int(h/5)))


print(sift_keypoint(img1,img2))
