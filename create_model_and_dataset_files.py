import glob
import os
from pathlib import Path
from lxml.etree import Element, SubElement, tostring
import regex as re

_list_of_elements = ['LV', 'RV', 'LA', 'RA', 'AO', 'PA', 'MV', 'TV', 'AV', 'PV', 'APP', 'LIPV', 'LSPV', 'RSPV', 'RIPV',
                     'SVC', 'IVC']


class BuildXML:

    def __init__(self, source='data', key_word=None,  list_of_elements=None):

        self.source = source
        self.output = self.source
        self.list_of_elements = list_of_elements
        self.key_word = key_word
        self.element_files = []
        self.elem = ''
        self.files = None
        self.current_id = None
        self.top = None

    def find_elements(self):

        list_of_elements_with_id = []
        for f in self.files:
            if self.current_id in f:
                list_of_elements_with_id.append(f)
        return list_of_elements_with_id

    def find_ids(self):

        list_of_ids = []
        for filename in self.files:
            file_id = re.findall(r'\d+', filename)
            list_of_ids.append(file_id[0],)
        return list_of_ids

    def get_element_filename(self):

        found_element_file = []
        for element_file in self.element_files:
            if self.elem in element_file:
                found_element_file = element_file
                return found_element_file
        if not found_element_file:
            exit('Element {} in subject {} is missing!'.format(self.elem, self.current_id))

    def write_xml(self, output=None):

        if output is not None:
            self.output = output
        filename = os.path.join(self.output, (self.top.tag+'.xml').replace('-', '_'))
        pretty_top = tostring(self.top, pretty_print=True, xml_declaration=True)
        with open(filename, 'wb') as f:
            f.write(pretty_top)


class DataSet(BuildXML):

    def __init__(self, source='data', key_word=None,  list_of_elements=None):

        super().__init__(source, key_word, list_of_elements)

        self.files = glob.glob(os.path.join(self.source, '*.vtk'))
        self.files.sort()
        self.number_of_cases = len(self.files)
        self.ids = list(set(self.find_ids()))
        self.ids.sort()
        self.current_id = self.ids[0]
        self.element_files = []
        self.elem = ''
        self.structure = ''

    def build_with_lxml_tree(self):
        self.top = Element('data-set')
        for self.current_id in self.ids:
            self.element_files = self.find_elements()

            subject = SubElement(self.top, 'subject', id='sub{}'.format(self.current_id))
            visit = SubElement(subject, 'visit', id='varifold')
            if self.element_files:
                for element in self.list_of_elements:
                    self.elem = '_' + element
                    filename = SubElement(visit, 'filename', object_id=element)
                    filename.text = self.get_element_filename()
            else:
                filename = SubElement(visit, 'filename', object_id=self.key_word)
                filename.text = glob.glob(os.path.join(self.source, '{}.vtk'.format(self.current_id)))


class Model(BuildXML):

    def __init__(self, source='data', key_word=None, list_of_elements=None, prototype_id=None,
                 deformation_kernel_width=10, prototype_kernel_width=10, noise_std=0.1):

        super().__init__(source, key_word, list_of_elements)

        self.deformation_kernel_width = str(deformation_kernel_width)
        self.prototype_kernel_width = str(prototype_kernel_width)
        self.noise_std = str(noise_std)
        self.prototype_id = str(prototype_id).zfill(2)
        self.files = []
        if not list_of_elements:
            self.files = glob.glob(os.path.join(source, '*{}*.vtk'.format(self.prototype_id)))
        else:
            for elem in list_of_elements:
                self.elem = elem
                element_files = glob.glob(os.path.join(source, '*{}*_{}.vtk'.format(self.prototype_id, self.elem)))
                self.files.extend(element_files)
        self.files.sort()
        self.number_of_cases = len(self.files)
        self.ids = self.find_ids()
        self.current_id = self.ids[0]

    def insert_default_branches(self, obj):
        dot = SubElement(obj, 'deformable-object-type')
        dot.text = 'Polyline'
        at = SubElement(obj, 'attachment-type')
        at.text = 'Varifold'
        kernel_width = SubElement(obj, 'kernel-width')
        kernel_width.text = self.prototype_kernel_width
        kernel_type = SubElement(obj, 'kernel-type')
        kernel_type.text = 'keops'
        noise_st = SubElement(obj, 'noise-std')
        noise_st.text = self.noise_std

    def build_with_lxml_tree(self):

        self.top = Element('model')
        model_type = SubElement(self.top, 'model-type')
        model_type.text = 'DeterministicAtlas'
        dimension = SubElement(self.top, 'dimension')
        dimension.text = '3'
        template = SubElement(self.top, 'template')

        self.element_files = self.find_elements()

        if self.element_files:
            for element in self.list_of_elements:
                self.elem = '_' + element
                obj = SubElement(template, 'object', id=element)
                self.insert_default_branches(obj)
                filename = SubElement(obj, 'filename')
                filename.text = self.get_element_filename()
        else:
            obj = SubElement(template, 'object', id=self.key_word)
            self.insert_default_branches()
            filename = SubElement(obj, 'filename')
            filename.text = self.files[0]

        deformation_parameters = SubElement(self.top, 'deformation-parameters')
        kernel_width = SubElement(deformation_parameters, 'kernel-width')
        kernel_width.text = self.deformation_kernel_width
        kernel_type = SubElement(deformation_parameters, 'kernel-type')
        kernel_type.text = 'keops'


class ModelShooting(BuildXML):
    def __init__(self, source='data', key_word=None, list_of_elements=None, momenta_filename=None,
                 deformation_kernel_width=10):

        super().__init__(source, key_word, list_of_elements)
        self.momenta_file = os.path.join(source, momenta_filename)
        self.deformation_kernel_width = str(deformation_kernel_width)
        self.files = []
        if not list_of_elements:
            self.files = glob.glob(os.path.join(source, '*.vtk'))
        else:
            for elem in list_of_elements:
                self.elem = elem
                element_files = glob.glob(os.path.join(source, '*_{}.vtk'.format(self.elem)))
                self.files.extend(element_files)
        self.files.sort()
        self.number_of_cases = len(self.files)
        self.ids = self.find_ids()
        self.current_id = self.ids[0]

    def build_with_lxml_tree(self):

        self.top = Element('model')
        model_type = SubElement(self.top, 'model-type')
        model_type.text = 'Shooting'
        dimension = SubElement(self.top, 'dimension')
        dimension.text = '3'
        template = SubElement(self.top, 'template')

        self.element_files = self.find_elements()

        if self.element_files:
            for element in self.list_of_elements:
                self.elem = '_' + element
                obj = SubElement(template, 'object', id=element)
                filename = SubElement(obj, 'filename')
                dot = SubElement(obj, 'deformable-object-type')
                dot.text = 'Polyline'
                filename.text = self.get_element_filename()
        else:
            obj = SubElement(template, 'object', id=self.key_word)
            filename = SubElement(obj, 'filename')
            dot = SubElement(obj, 'deformable-object-type')
            dot.text = 'Polyline'
            filename.text = self.files[0]

        initial_control_points = SubElement(self.top, 'initial-control-points')
        initial_control_points.text = os.path.join(self.source,
                                                   'DeterministicAtlas__EstimatedParameters__ControlPoints.txt')
        initial_momenta = SubElement(self.top, 'initial-momenta')
        initial_momenta.text = os.path.join(self.source, self.momenta_file)
        deformation_parameters = SubElement(self.top, 'deformation-parameters')
        kernel_width = SubElement(deformation_parameters, 'kernel-width')
        kernel_width.text = self.deformation_kernel_width
        kernel_type = SubElement(deformation_parameters, 'kernel-type')
        kernel_type.text = 'keops'


if __name__ == '__main__':

    # ds = DataSet(source=os.path.join(str(Path.home()), 'Python', 'data', 'case_', 'aligned_meshes'),
    #              key_word='case_',
    #              list_of_elements=_list_of_elements)
    # ds.build_with_lxml_tree()
    # ds.write_xml('/home/mat/Deformetrica/deterministic_atlas_ct/')
    #
    # mdl = Model(source=os.path.join(str(Path.home()), 'Python', 'data', 'case_', 'aligned_meshes'),
    #             key_word='case_',
    #             prototype_id=3, list_of_elements=_list_of_elements,
    #             deformation_kernel_width=10,
    #             prototype_kernel_width=10)
    # mdl.build_with_lxml_tree()
    # mdl.write_xml('/home/mat/Deformetrica/deterministic_atlas_ct/')

    mom_mdl = ModelShooting(source=os.path.join(str(Path.home()), 'Deformetrica', 'deterministic_atlas_ct',
                                                'output_separate_tmp10_def10_prttpe8_aligned', 'Decomposition'),
                            key_word='Template',
                            momenta_filename='Extreme_Momenta.txt',
                            list_of_elements=_list_of_elements,
                            deformation_kernel_width=10)
    print(mom_mdl.source)
    mom_mdl.build_with_lxml_tree()
    mom_mdl.write_xml('/home/mat/Deformetrica/deterministic_atlas_ct/')