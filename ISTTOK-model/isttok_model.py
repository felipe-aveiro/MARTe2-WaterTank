from cadquery.vis import show
import paramak # parameters are in millimiters

# major_radius = R_central_sol + layer_inner_GAP + thickness_copper + thickness_INCONEL + layer_vessel&plasma_GAP + layer_PLASMA / 2

# Main ISTTOK's geometric parameters
"""
major radius = 460 mm 
minor radius = 85 mm
copper shell diameter = 210 mm - - -> center_to_outer_copper_shell = major radius - copper shell diameter/2 = 355 mm
central solenoid radius = ?
"""

center_to_outer_copper_shell = float(355)
central_solenoid = float(180)
coil_colors = [(1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 0.5, 0.0, 0.75), (1.0, 0.5, 0.0, 0.75), (1.0, 0.5, 0.0), (1.0, 0.5, 0.0), (1.0, 1.0, 0.75), (1.0, 1.0, 0.75)]

extra_cut_shapes = []
for case_thickness, height, width, center_point in zip(
    [10, 10, 10, 10, 10, 10, 10, 10], [20, 20, 5, 5, 20, 20, 5, 5], [20, 20, 20, 20, 20, 20, 20, 20],
    [(620, 130), (620, -130), (580, 82.5), (580, -82.5), (340, 70), (340, -70), (580, 57.5), (580, -57.5)]
):
    extra_cut_shapes.append(
        paramak.poloidal_field_coil(
            height=height, width=width, center_point=center_point, rotation_angle=270
        )
    )
    extra_cut_shapes.append(
        paramak.poloidal_field_coil_case(
            coil_height=height,
            coil_width=width,
            casing_thickness=case_thickness,
            rotation_angle=270,
            center_point=center_point,
            color=coil_colors,
        )
    )

isttok = paramak.tokamak_from_plasma(
    radial_build = [
        (paramak.LayerType.SOLID, central_solenoid), # central solenoid radius
        (paramak.LayerType.GAP, center_to_outer_copper_shell - central_solenoid), # gap between central solenoid and copper shell
        (paramak.LayerType.SOLID, 15), # copper shell thickness
        (paramak.LayerType.GAP, 4.85), # gap between copper shell and INCONEL alloy
        (paramak.LayerType.SOLID, 0.15), # INCONEL alloy thickness
        (paramak.LayerType.GAP, 25), # gap between INCONEL alloy and plasma
        (paramak.LayerType.PLASMA, 120), # plasma's diameter
        (paramak.LayerType.GAP, 25), # gap between plasma and INCONEL alloy
        (paramak.LayerType.SOLID, 0.15), # INCONEL alloy thickness
        (paramak.LayerType.GAP, 4.85), # gap between INCONEL alloy and copper shell
        (paramak.LayerType.SOLID, 15), # copper shell thickness
    ],
    elongation=1.0,
    triangularity=0.0,
    rotation_angle=270.0,
    colors={
        "layer_1": (0.49, 0.13, 0.01), # central solenoid
        "layer_2": (0.80, 0.59, 0.36), # INCONEL layer
        "layer_3": (0.82, 0.82, 0.82, 0.95), # copper shell
        "plasma": (1.0, 0.7, 0.8, 0.6), # plasma
        "add_extra_cut_shape_1": (1.0, 1.0, 1.0), # inner shape upper primary coil
        "add_extra_cut_shape_2": (1.0, 1.0, 1.0), # outer shape upper primary coil
        "add_extra_cut_shape_3": (1.0, 1.0, 1.0), # inner shape lower primary coil
        "add_extra_cut_shape_4": (1.0, 1.0, 1.0), # outer shape lower primary coil
        "add_extra_cut_shape_5": (0.5, 0.5, 0.8), # inner shape upper horizontal coil (represented as the upper coil)
        "add_extra_cut_shape_6": (0.5, 0.5, 0.8), # outer shape upper horizontal coil (represented as the upper coil)
        "add_extra_cut_shape_7": (0.5, 0.5, 0.8), # inner shape lower horizontal coil (represented as the lower coil)
        "add_extra_cut_shape_8": (0.5, 0.5, 0.8), # outer shape lower horizontal coil (represented as the lower coil)
        "add_extra_cut_shape_9": (1.0, 0.5, 0.0), # inner shape upper inner vertical coil
        "add_extra_cut_shape_10": (1.0, 0.5, 0.0), # outer shape upper inner vertical coil
        "add_extra_cut_shape_11": (1.0, 0.5, 0.0), # inner shape lower inner vertical coil
        "add_extra_cut_shape_12": (1.0, 0.5, 0.0), # outer shape lower inner vertical coil
        "add_extra_cut_shape_13": (1.0, 0.5, 0.0), # inner shape upper outer vertical coil (represented as the lower coil)
        "add_extra_cut_shape_14": (1.0, 0.5, 0.0), # outer shape upper outer vertical coil (represented as the lower coil)
        "add_extra_cut_shape_15": (1.0, 0.5, 0.0), # inner shape lower outer vertical coil (represented as the upper coil)
        "add_extra_cut_shape_16": (1.0, 0.5, 0.0), # outer shape lower outer vertical coil (represented as the upper coil)
    },
    extra_cut_shapes=extra_cut_shapes
)

show(isttok)
#isttok.save(f"...\\ISTTOK.step")