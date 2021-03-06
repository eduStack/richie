import fetchMock from 'fetch-mock';

import { Course } from '../../types/Course';
import { handle } from '../../utils/errors/handle';
import { getSuggestionsSection } from './getSuggestionsSection';

const mockHandle: jest.Mock<typeof handle> = handle as any;
jest.mock('../../utils/errors/handle');

describe('utils/searchSuggest/getSuggestionsSection', () => {
  afterEach(() => {
    fetchMock.restore();
  });

  it('runs the search and builds a SearchSuggestionSection with the results', async () => {
    fetchMock.get('/api/v1.0/courses/?query=some%20search', {
      objects: [{ title: 'Course #1' }, { title: 'Course #2' }],
    });

    let suggestionsSection;
    try {
      suggestionsSection = await getSuggestionsSection(
        'courses',
        { defaultMessage: 'Courses', id: 'coursesHumanName' },
        'some search',
      );
    } catch (error) {
      fail('Did not expect getSuggestionsSection to fail');
    }

    expect(suggestionsSection).toEqual({
      message: { defaultMessage: 'Courses', id: 'coursesHumanName' },
      model: 'courses',
      values: [
        { title: 'Course #1' } as Course,
        { title: 'Course #2' } as Course,
      ],
    });
  });

  it('reports the error when the request fails', async () => {
    fetchMock.get('/api/v1.0/courses/?query=some%20search', {
      throws: 'Failed to send API request',
    });
    await getSuggestionsSection(
      'courses',
      { defaultMessage: 'Courses', id: 'coursesHumanName' },
      'some search',
    );
    expect(mockHandle).toHaveBeenCalledWith(
      new Error('Failed to send API request'),
    );
  });

  it('reports the error when the server returns an error code', async () => {
    fetchMock.get('/api/v1.0/courses/?query=some%20search', {
      body: {},
      status: 403,
    });
    await getSuggestionsSection(
      'courses',
      { defaultMessage: 'Courses', id: 'coursesHumanName' },
      'some search',
    );
    expect(mockHandle).toHaveBeenCalledWith(
      new Error('Failed to get list from /api/v1.0/courses/ : 403'),
    );
  });

  it('reports the error when it receives broken json', async () => {
    fetchMock.get('/api/v1.0/courses/?query=some%20search', 'not json');
    await getSuggestionsSection(
      'courses',
      { defaultMessage: 'Courses', id: 'coursesHumanName' },
      'some search',
    );
    expect(mockHandle).toHaveBeenCalledWith(
      new Error(
        'Failed to decode JSON in getSuggestionSection FetchError: invalid json response body at ' +
          '/api/v1.0/courses/?query=some%20search reason: Unexpected token o in JSON at position 1',
      ),
    );
  });
});
