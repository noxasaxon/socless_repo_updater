#### NOTE: run with cmd `tox -- --github`
# @pytest.mark.github
# def test_output_structure(mock_socless_info_output_as_dict):
#     mock_output = build_integration_classes_from_json(mock_socless_info_output_as_dict)
#     output = build_from_github(
#         "twilio-labs/socless",
#         output_file_path="socless_info.json",
#     )

#     # assert that it converts to json without error
#     output_as_json = output.json()
#     mock_output_as_json = mock_output.json()

#     # assert equality using dicts
#     assert json.loads(output_as_json) == json.loads(mock_output_as_json)


def test_pass():
    pass
