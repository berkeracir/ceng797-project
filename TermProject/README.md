# I used Anaconda and PyCharm for this project
# https://towardsdatascience.com/setting-up-python-platform-for-machine-learning-projects-cfd85682c54b
# https://machinelearningmastery.com/setup-python-environment-machine-learning-deep-learning-anaconda/

# Create a new Anaconda virtual environment
conda create -n myenv python=3.8

# For Windows
conda activate myenv
# For MAC OS
#source activate myenv

# Install General Libraries
conda install networkx
conda install scipy numpy matplotlib pandas statsmodels scikit-learn

# Install Deep Learning Libraries
conda install theano
conda install -c conda-forge tensorflow
pip install keras

# AHC Component: https://github.com/cengwins/ahc
