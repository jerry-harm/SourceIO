from ....utils.bpy_utils import is_blender_4
from ...shader_base import Nodes
from ..source1_shader_base import Source1ShaderBase

from .detail import DetailSupportMixin


class WorldVertexTransition(DetailSupportMixin, Source1ShaderBase):
    SHADER = 'worldvertextransition'

    @property
    def basetexture(self):
        texture_path = self._vmt.get_string('$basetexture', None)
        if texture_path is not None:
            return self.load_texture_or_default(texture_path, (0.3, 0.0, 0.3, 1.0))
        return None
    
    @property
    def blendmodulatetexture(self):
        texture_path = self._vmt.get_string('$blendmodulatetexture', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.3, 0.0, 0.3, 1.0))
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = 'Non-Color'
            return image

        return None

    @property
    def basetexture2(self):
        texture_path = self._vmt.get_string('$basetexture2', None)
        if texture_path is not None:
            return self.load_texture_or_default(texture_path, (0.3, 0.3, 0.0, 1.0))
        return None

    @property
    def bumpmap(self):
        texture_path = self._vmt.get_string('$bumpmap', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.6, 0.0, 0.6, 1.0))
            if self.ssbump:
                image = self.convert_ssbump(image)
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = 'Non-Color'
            return image
        return None

    @property
    def bumpmap2(self):
        texture_path = self._vmt.get_string('$bumpmap2', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.6, 0.6, 0.0, 1.0))
            if self.ssbump:
                image = self.convert_ssbump(image)
            image.colorspace_settings.is_data = True
            image.colorspace_settings.name = 'Non-Color'
            return image
        return None
    
    @property
    def detail(self):
        texture_path = self._vmt.get_string('$detail', None)
        if texture_path is not None:
            image = self.load_texture_or_default(texture_path, (0.6, 0.6, 0.0, 1.0))
            return image
        return None

    @property
    def selfillum(self):
        return self._vmt.get_int('$selfillum', 0) == 1

    @property
    def ssbump(self):
        return self._vmt.get_int('ssbump', 0) == 1

    @property
    def translucent(self):
        return self._vmt.get_int('$translucent', 0) == 1

    @property
    def alpha(self):
        return self._vmt.get_float('alpha', 1.0)

    @property
    def phong(self):
        return self._vmt.get_int('$phong', 0) == 1

    @property
    def phongboost(self):
        return self._vmt.get_float('$phongboost', 1)

    def create_nodes(self, material):
        if super().create_nodes(material) in ['UNKNOWN', 'LOADED']:
            return

        material_output = self.create_node(Nodes.ShaderNodeOutputMaterial)
        shader = self.create_node(Nodes.ShaderNodeBsdfPrincipled, self.SHADER)
        self.connect_nodes(shader.outputs['BSDF'], material_output.inputs['Surface'])

        basetexture = self.basetexture
        basetexture2 = self.basetexture2

        if basetexture and basetexture2:
            vertex_color = self.create_node(Nodes.ShaderNodeVertexColor)
            
            color_mix = self.create_node(Nodes.ShaderNodeMixRGB)
            if self.blendmodulatetexture != None:
                SEPrgb = self.create_node(Nodes.ShaderNodeSeparateRGB)
                sub = self.create_node(Nodes.ShaderNodeMath)
                sub.operation = 'SUBTRACT'
                add = self.create_node(Nodes.ShaderNodeMath)
                add.operation = 'ADD'
                maprange = self.create_node(Nodes.ShaderNodeMapRange)
                maprange.interpolation_type = 'SMOOTHSTEP'

                self.connect_nodes(SEPrgb.outputs[1], sub.inputs[0])
                self.connect_nodes(SEPrgb.outputs[0], sub.inputs[1])
                self.connect_nodes(SEPrgb.outputs[0], add.inputs[0])
                self.connect_nodes(SEPrgb.outputs[1], add.inputs[1])
                self.connect_nodes(sub.outputs[0], maprange.inputs[1])
                self.connect_nodes(add.outputs[0], maprange.inputs[2])
                self.connect_nodes(vertex_color.outputs[0], maprange.inputs[0])
                self.connect_nodes(maprange.outputs[0], color_mix.inputs['Fac'])

                self.create_and_connect_texture_node(self.blendmodulatetexture, SEPrgb.inputs[0], name='$blendmodulatedecal')

                #self.create_texture_node(self.blendmodulatetexture, '$blendmodulatedecal')
            else:
                self.connect_nodes(vertex_color.outputs['Color'], color_mix.inputs['Fac'])
            color_mix.blend_type = 'MIX'

            albedo = color_mix.outputs[0]

            self.create_and_connect_texture_node(basetexture,
                                                 color_mix.inputs['Color1'],
                                                 name='$basetexture')
            self.create_and_connect_texture_node(basetexture2,
                                                 color_mix.inputs['Color2'],
                                                 name='$basetexture2')
            
            if self.detail:
                albedo, detail = self.handle_detail(shader.inputs['Base Color'], albedo, uv_node=None)
            else:
                self.connect_nodes(color_mix.outputs['Color'], shader.inputs['Base Color'])

        if not self.phong:
            if is_blender_4():
                shader.inputs['Specular IOR Level'].default_value = 0
            else:
                shader.inputs['Specular'].default_value = 0
