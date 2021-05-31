import React, { useMemo, useCallback, ChangeEvent } from 'react';
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles';

// Components
import BeBox from '@binaryedge/core/BeBox';
import BeFlex from '@binaryedge/core/BeFlex';
import BeText from '@binaryedge/core/BeText';

// MUI
import Select from '@material-ui/core/Select';
import MenuItem from '@material-ui/core/MenuItem';
import Pagination from '@material-ui/lab/Pagination';

import formatNumber from '@binaryedge/helpers/formatNumber';

// Styles
const useStyles = ({}: Partial<MasterTablePaginationProps>) =>
  makeStyles(({}: Theme) =>
    createStyles({
      pageSizeSelect: {
        marginLeft: '0.25rem',
        marginRight: '1rem',
        '& .MuiSelect-select': {
          paddingTop: 10,
          paddingBottom: 10,
        },
      },
    }),
  )();

export const MasterTablePagination = ({
  id,
  rowCount,
  page,
  rowsPerPage,
  rowsPerPageOptions = [],
  changeRowsPerPage,
  changePage,
}: MasterTablePaginationProps) => {
  const classes = useStyles({});

  const maxPage = useMemo<number>(
    () => Math.floor(rowCount / rowsPerPage) + 1,
    [rowCount, rowsPerPage],
  );

  const handleOnChangePage = useCallback(
    (event: ChangeEvent<unknown>, newPage: number) => {
      changePage(newPage);
    },
    [changePage],
  );

  const handleOnChangePageSize = useCallback(
    (event: ChangeEvent<any>) => {
      changeRowsPerPage(parseInt(event?.target?.value, 10));
      changePage(1);
    },
    [changePage, changeRowsPerPage],
  );

  return (
    <tfoot>
      <tr>
        <td>
          <BeBox mt={2} mb={1} mr={4}>
            <BeFlex container alignItems="center" justify="flex-end">
              <BeFlex item>
                <Pagination
                  page={page}
                  count={maxPage}
                  siblingCount={2}
                  onChange={handleOnChangePage}
                />
              </BeFlex>
              <BeFlex item>
                <Select
                  id={id}
                  value={rowsPerPage}
                  variant="outlined"
                  onChange={handleOnChangePageSize}
                  className={classes.pageSizeSelect}
                >
                  {rowsPerPageOptions.map((value) => (
                    <MenuItem key={value} value={value}>
                      {value}
                    </MenuItem>
                  ))}
                </Select>
              </BeFlex>
              <BeFlex item>
                <BeText variant="body2">
                  {formatNumber(rowCount, '0,0')} Results
                </BeText>
              </BeFlex>
            </BeFlex>
          </BeBox>
        </td>
      </tr>
    </tfoot>
  );
};

export interface MasterTablePaginationProps {
  id: string;
  rowCount: number;
  page: number;
  rowsPerPage: number;
  rowsPerPageOptions: number[];
  changeRowsPerPage: (page: string | number) => void;
  changePage: (newPage: number) => void;
}

export default MasterTablePagination;