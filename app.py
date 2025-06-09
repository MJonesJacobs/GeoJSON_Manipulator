import viktor as vkt
from json import load,dumps
import kml2geojson
from datetime import datetime

def alter_input(params,json,**kwargs):
    # Sort
    if params.section_2.property_sort_option != None:
        rev = False if params.section_2.sort_type == "Ascending" else True
        try:
            json['features'].sort(key=lambda feature: float(feature['properties'][params.section_2.property_sort_option]),reverse=rev)
        except:
            json['features'].sort(key=lambda feature: feature['properties'][params.section_2.property_sort_option],reverse=rev)

    if params.section_2.Convert_Linestrings_to_Poly == True:
        for feature in json['features']:
            if feature['geometry']['type'] == 'LineString':
                # Ensure the coordinates form a closed loop
                coordinates = feature['geometry']['coordinates']
                if coordinates[0] != coordinates[-1]:
                    coordinates.append(coordinates[0])
                
                # Convert LineString to Polygon
                feature['geometry']['type'] = 'Polygon'
                feature['geometry']['coordinates'] = [coordinates]

    return json  

def get_json_properties_options(params, **kwargs):
    # Determine Filepath
    if params.section_1.file == None:
        return []
    if str(params.section_1.file.filename).endswith(".json"):
        json = params.section_1.file.file
        with json.open() as filedata:
            input_json = load(filedata)

    elif str(params.section_1.file.filename).endswith(".kml"):
        kml = params.section_1.file.file
        with kml.open() as filedata:
            input_json = kml2geojson.convert(filedata)[0]

    return list(input_json['features'][0]['properties'].keys())

def get_json_feature_types_options(params, **kwargs):
    # Determine Filepath
    if params.section_1.file == None:
        return []
    if str(params.section_1.file.filename).endswith(".json"):
        json = params.section_1.file.file
        with json.open() as filedata:
            input_json = load(filedata)
    elif str(params.section_1.file.filename).endswith(".kml"):
        kml = params.section_1.file.file
        with kml.open() as filedata:
            input_json = kml2geojson.convert(filedata)[0]

    unique_features = set()
    for feature in input_json['features']:
        unique_features.add(feature["geometry"]["type"])
    return list(unique_features)


def generate_json(params, **kwargs):
    # Convert GeoJSON to DataFrame
    if str(params.section_1.file.filename).endswith(".json"):
        json = params.section_1.file.file
        with json.open() as filedata:
            input_json = load(filedata)
    elif str(params.section_1.file.filename).endswith(".kml"):
        kml = params.section_1.file.file
        with kml.open() as filedata:
            input_json = kml2geojson.convert(filedata)[0]
    
    json = alter_input(params=params,json=input_json)

    return json

def generate_df(params, **kwargs):
    # Convert GeoJSON to DataFrame
    if str(params.section_1.file.filename).endswith(".json"):
        json = params.section_1.file.file
        with json.open() as filedata:
            input_json = load(filedata)
    elif str(params.section_1.file.filename).endswith(".kml"):
        kml = params.section_1.file.file
        with kml.open() as filedata:
            input_json = kml2geojson.convert(filedata)[0]
    
    json = alter_input(params=params,json=input_json)

    features = json['features']
    data = []
    top_row = list(features[0]['properties'].keys())
    top_row.insert(0,"id")
    data.append(top_row)
    for feature in features:
        row = list(feature['properties'].values())
        row = [str(x) for x in row]
        row.insert(0,feature["id"])
        data.append(row)
    return data

def file_root(params, **kwargs):
    return params.section_1.filename



_file_dependent_visible = vkt.And(
    vkt.IsNotEqual(vkt.Lookup('section_1.file'),None)
)

_sort_dependent_visible = vkt.And(
    vkt.IsNotEqual(vkt.Lookup('section_2.property_sort_option'),None)
)

_download_visible = vkt.And(
    vkt.IsEqual(vkt.Lookup('section_3.do_download_file'),True)
)
class Parametrization(vkt.Parametrization):
    section_1 = vkt.Section('File Upload')
    section_1.file = vkt.FileField('Upload a Kml or GeoJSON File',file_types=[".kml",".json"])
    # featuretype_options = vkt.MultiSelectField("Select geometry types to include",options=get_json_feature_types_options)
    # property_options = vkt.MultiSelectField('Json Properties to Include', options=get_json_properties_options)
    section_2 = vkt.Section('GeoJSON Manipulation')
    section_2.Convert_Linestrings_to_Poly = vkt.BooleanField('Convert Linestrings to Polygons?',description="Linestrings will all be converted to polygons. This converts closed linestrings into polygons.",visible=_file_dependent_visible)
    section_2.property_sort_option = vkt.OptionField('Properties to Sort by Include', options=get_json_properties_options,description="Select one of the common feature properties you wish to sort by. This will be used to rearrange the order of the GeoJSON file",visible=_file_dependent_visible)
    section_2.sort_type = vkt.OptionField("Sort Type",options=["Ascending","Descending"],description="Determines the order the selected property is sorted by",default="Ascending",visible=_sort_dependent_visible)
    
    
    section_3 = vkt.Section('GeoJSON Download')
    section_3.do_download_file = vkt.BooleanField('Download Updated GeoJSON',description="Select yes to display inputs needed to download new json",visible=_file_dependent_visible)
    # section_3.download_file_name = vkt.OutputField("")
    section_3.download_button = vkt.DownloadButton("Download Updated GeoJSON FIle", method="download_json",visible=_download_visible)
    pass # Welcome to VIKTOR! You can add your input fields here. Happy Coding!


class Controller(vkt.Controller):
    parametrization = Parametrization

    @vkt.GeoJSONView('GeoJSON view',duration_guess=10)
    def get_geojson_view(self, params, **kwargs):
        if params.section_1.file == None:
            return vkt.GeoJSONResult({
                "type": "FeatureCollection",
                "features": []
            })
        json = generate_json(params=params)
        return vkt.GeoJSONResult(json)

    @vkt.TableView("GeoJSON Properties",duration_guess=10)
    def table_view(self, params, **kwargs):
        if params.section_1.file == None:
            return vkt.TableResult(
                data=[["Please Upload a File to Preview Properties"]],
                enable_sorting_and_filtering=False
                )
        else:
            df=generate_df(params=params)
            return vkt.TableResult(
                data=df[1::],
                column_headers=df[0],
                enable_sorting_and_filtering=False
                )
    
    def download_json(self, params, **kwargs):
        json = generate_json(params=params)
        json_str = dumps(json)
        filename = str(params.section_1.file.filename)
        for suffix in [".json",".kml"]:
            filename = filename.removesuffix(suffix)
        now = datetime.now()
        formatted_date_time = now.strftime("%Y%m%d_%H%M")
        return vkt.DownloadResult(json_str, f'{filename}_vkt_{formatted_date_time}.json')

