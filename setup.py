from setuptools import setup,find_packages


# python setup.py bdist_wheel
setup(
    name='mathai',
    version='1.0.3',
    description='mathai server,smartchoose',

    py_modules=[],
    packages=find_packages(),
    install_requires=['jproperties','pymysql','django','django_crontab'],
    scripts=[],

    author='zhang xiao kai',
    author_email='mckj_zhangxk@163.com'

)
