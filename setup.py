from setuptools import setup

setup(
    name='uggaugga_client',
    version='0.1.0',    
    description='Client for uggaugga service',
    url='https://github.com/greenapes/uggaugga_client',
    author='Marco Pretelli',
    author_email='lordscapoladestra@gmail.com   ',
    license='BSD 2-clause',
    packages=['uggaugga'],
    install_requires=['requests',
                      ],
    scripts=['bin/sync'],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)