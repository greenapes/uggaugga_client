from setuptools import setup

setup(
    name='uggaugga_client',
    version='0.3.0',    
    description='Client for uggaugga service',
    url='https://github.com/greenapes/uggaugga_client',
    author='Marco Pretelli',
    author_email='lordscapoladestra@gmail.com',
    license='MIT',
    packages=['uggaugga_client'],
    install_requires=['requests'],
    scripts=['bin/uggaugga'],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  
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
        'Programming Language :: Python :: 3.12',
    ],
)