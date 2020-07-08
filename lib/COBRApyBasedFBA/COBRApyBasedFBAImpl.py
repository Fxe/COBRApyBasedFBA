# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import logging
import os
from pprint import pformat

from installed_clients.KBaseReportClient import KBaseReport
from COBRApyBasedFBA.fba_pipeline import FBAPipeline
from cobrakbase.core.converters import KBaseFBAModelToCobraBuilder
import cobrakbase
#END_HEADER


class COBRApyBasedFBA:
    '''
    Module Name:
    COBRApyBasedFBA

    Module Description:
    A KBase module: COBRApyBasedFBA
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/kbaseapps/COBRApyBasedFBA.git"
    GIT_COMMIT_HASH = "fc95a9b732d93775b4afb4ef4f80952c2bdfd8c3"

    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        
        # Any configuration parameters that are important should be parsed and
        # saved in the constructor.
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_fba_pipeline(self, ctx, params):
        """
        Run flux balance analysis and return ID of FBA object with results
        :param params: instance of type "RunFBAPipelineParams" -> structure:
           parameter "fbamodel_id" of type "fbamodel_id" (A string
           representing a FBAModel id.), parameter "fbamodel_workspace" of
           type "workspace_name" (A string representing a workspace name.),
           parameter "media_id" of type "media_id" (A string representing a
           Media id.), parameter "media_workspace" of type "workspace_name"
           (A string representing a workspace name.), parameter
           "target_reaction" of type "reaction_id" (A string representing a
           reaction id.), parameter "fba_output_id" of type "fba_id" (A
           string representing a FBA id.), parameter "workspace" of type
           "workspace_name" (A string representing a workspace name.),
           parameter "solver" of String, parameter "minimize_objective" of
           type "bool" (A binary boolean), parameter "fva" of type "bool" (A
           binary boolean), parameter "minimize_flux" of type "bool" (A
           binary boolean), parameter "loopless_fba" of type "bool" (A binary
           boolean), parameter "loopless_fva" of type "bool" (A binary
           boolean), parameter "simulate_ko" of type "bool" (A binary
           boolean), parameter "all_reversible" of type "bool" (A binary
           boolean), parameter "fraction_of_optimum_pfba" of Double,
           parameter "fraction_of_optimum_fva" of Double, parameter
           "feature_ko_list" of list of type "feature_id" (A string
           representing a feature id.), parameter "reaction_ko_list" of list
           of type "reaction_id" (A string representing a reaction id.),
           parameter "media_supplement_list" of list of type "compound_id" (A
           string representing a compound id.), parameter
           "objective_fraction" of Double, parameter "max_c_uptake" of
           Double, parameter "max_n_uptake" of Double, parameter
           "max_p_uptake" of Double, parameter "max_s_uptake" of Double,
           parameter "max_o_uptake" of Double, parameter "default_max_uptake"
           of Double
        :returns: instance of type "RunFBAPipelineResults" -> structure:
           parameter "new_fba_ref" of type "ws_fba_id" (The workspace ID for
           a FBA data object. @id ws KBaseFBA.FBA), parameter "objective" of
           Long, parameter "report_name" of String, parameter "report_ref" of
           type "ws_report_id" (The workspace ID for a Report object @id ws
           KBaseReport.Report)
        """
        # ctx is the context object
        # return variables are: results
        #BEGIN run_fba_pipeline

        # TODO: for debugging
        print('PARAMS')
        print(params)

        # TODO: temp fix. Filipe's problem
        if params['target_reaction'] == 'bio1':
          params['target_reaction'] += '_biomass'

        # TODO: this is temp fix. UI does not contain workspace. update spec
        params['fbamodel_workspace'] = params['workspace']
        params['media_workspace'] = params['workspace']

        # TODO: toggle dev=False when we test on production
        kbase = cobrakbase.KBaseAPI(ctx['token'], dev=True)
        ref = kbase.get_object_info_from_ref(params['fbamodel_id'])
        fbamodel_json = kbase.get_object(ref.id, ref.workspace_id)
        fbamodel = cobrakbase.core.model.KBaseFBAModel(fbamodel_json)
        
        # Retrieve media
        ref = kbase.get_object_info_from_ref(params['media_id'])
        media_json = kbase.get_object(ref.id, ref.workspace_id)
        media = cobrakbase.core.KBaseBiochemMedia(media_json)

        # TODO: add extra compounds to media with params['media_supplement_list']
        #       see what these params look like

        builder = KBaseFBAModelToCobraBuilder(fbamodel)
        model = builder.with_media(media).build()

        pipeline = FBAPipeline.fromKBaseParams(params)
        # Result is fba type object
        result = pipeline.run(model, media)
        # kbase_ref is list of lists with only one inner list
        kbase_ref = kbase.save_object(result['id'], params['workspace'], 'KBaseFBA.FBA', result)

        # Step 5 - Build a Report and return
        reportObj = {
            'objects_created': [{'ref': f"{params['workspace']}/{params['fba_output_id']}",
                                 'description': 'FBA'}],
            'text_message': 'TODO: print FBA solution, etc'
        }
        print("callback_url: ", self.callback_url)
        report = KBaseReport(self.callback_url)
        # TODO: create_extended_report function
        report_info = report.create({'report': reportObj, 'workspace_name': params['workspace']})

        # STEP 6: contruct the output to send back
        results = {'report_name': report_info['name'],
                   'report_ref': report_info['ref'],
                   'workspace_name': params['workspace'],
                   'ws': params['workspace'],
                   'type': 'KBaseFBA.FBA',
                   'obj': params['fba_output_id']
                  }

        #END run_fba_pipeline

        # At some point might do deeper type checking...
        if not isinstance(results, dict):
            raise ValueError('Method run_fba_pipeline return value ' +
                             'results is not type dict as required.')
        # return the results
        return [results]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
