from setuptools import setup, find_packages

setup(
    name='subfeed-sharekit',
    version='1.0.0',
    description='Custom ShareKit Clone with UTM popup and preview redirection',
    author='antoancms',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'flask-cors'
    ],
    entry_points={
        'console_scripts': [
            'runsharekit=app:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License'
    ],
    python_requires='>=3.7',
)
