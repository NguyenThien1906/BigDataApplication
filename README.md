# Anime recommendation for users based on user rating

Analyze and process user ratings on anime user titles using Big Data and Machine Learning tools.

This project is based on school assignment by PhD. Bùi Duy Đăng. More information on the assignment is in *Project Description.pdf*.

## Authors
| Student ID | Name | Main tasks |
|---|---|---|
| 21127170 | Nguyễn Thế Thiện| Pre-processing |
| 21127326 | Nguyễn Trần Trung Kiên | Model research & implementation |
| 21127329 | Châu Tấn Kiệt| Model comparisons & evaluations |

&copy; 2025 Ho Chi Minh University of Science - VNU.

## Work summary

**Detailed work is fully documented in *report.pdf*. For a summary on what we conduct on our project, you can view our graphical presentation in *slides.pdf*.**

We perform data pre-processing on a large static dataset (> 1 GB worth of data in relational database), then train basic recommendation model in order to conduct experimental comparisons & evaluations. Then the chosen model is used to recommend a list of anime given user ID as the input.

The work is as follows:

### Data pre-processing
![Images](/Big%20Data%20Application/git/images/prep1.png)

We use [Anime Dataset 2023](https://www.kaggle.com/datasets/dbdmobile/myanimelist-dataset?resource=download) from Kaggle as a collection of user ratings, and registered users and anime titles on MyAnimeList - one of the biggest anime platforms.

In summary, we extract user and anime features from user and anime information files (**user-details-2023.csv**, **anime-dataset-2023.csv**), then join with user ratings (**users-score-2023.csv**) to a unified dataset. This unified dataset shall be slightly altered to match model input form.

### Model research
![ALS model](/Big%20Data%20Application/git/images/model1.png)

Alternating Least Squares (ALS) is a Matrix Factorization model by using matrix multiplication approximation. The whole purpose is to guess the missing ratings based on the underlying patterns in the given ratings.

### Model insights

#### Recommendation list

![Recommendation list for user 834209](/Big%20Data%20Application/git/images/insight1.png)

![Genre distribution in recommendation list for user 834209](/Big%20Data%20Application/git/images/insight2.png)

![Prediction results for all users](/Big%20Data%20Application/git/images/insight3.png)

#### Model comparison

![Comparison: ALS vs. SVD](/Big%20Data%20Application/git/images/insight4.png)



