from setuptools import setup, find_packages


description = ('A Python implementation of the two player strategic board game '
               'Abalone.')

with open('README.md') as readme:
    long_description = readme.read()


setup(
    name='abalone',
    version='0.1',
    description=description,
    long_description=long_description,
    author='Unai Zalakain',
    author_email='unai@gisa-elkartea.com',
    url='http://github.com/unaizalakain/abalone/',
    packages=find_packages(exclude=('tests*',)),
    package_data = {},
    license='GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Games/Entertainment :: Board Games',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    include_package_data=True,
    zip_safe=False,
)
