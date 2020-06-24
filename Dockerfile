FROM kbase/kbase:sdkbase.latest
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update

# Here we install a python coverage tool and an
# https library that is out of date in the base image.

FROM python:3.7

RUN pip install coverage

# update security libraries in the base image
RUN pip install --upgrade pip setuptools wheel cffi
RUN pip install --upgrade pyopenssl ndg-httpsclient
RUN pip install --upgrade pyasn1 requests 'requests[security]'

# Install forked version of optlang and cobrapy to add
# additional solver support COINOR-CBC,CLP and OSQP
RUN mkdir deps && cd deps
RUN git clone https://github.com/braceal/optlang.git
RUN cd optlang && git checkout test/coinor-cbc_osqp && cd ..
RUN git clone https://github.com/braceal/cobrapy.git
RUN cd cobrapy && git checkout feature/coinor-cbc_osqp && cd ..
RUN pip install optlang/
RUN pip install cobrapy/ && cd ..
RUN pip install cobrakbase==0.2.5

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
